import os

import pytest

from smart_file_sorter.categories import category_for
from smart_file_sorter.sorter import build_plan, apply_plan


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("photo.JPG", "Images"),
        ("report.pdf", "Documents"),
        ("data.csv", "Spreadsheets"),
        ("deck.pptx", "Presentations"),
        ("song.mp3", "Audio"),
        ("clip.mp4", "Video"),
        ("bundle.zip", "Archives"),
        ("main.py", "Code"),
        ("app.log", "Data"),
        ("mystery", "Other"),
        (".gitignore", "Other"),
        ("weird.zzz", "Other"),
    ],
)
def test_category_for(filename, expected):
    assert category_for(filename) == expected


def _touch(directory, name, content="x"):
    with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
        handle.write(content)


def test_build_plan_groups_and_counts(tmp_path):
    d = str(tmp_path)
    _touch(d, "a.jpg")
    _touch(d, "b.png")
    _touch(d, "c.pdf")
    _touch(d, "script.py")

    plan = build_plan(d)

    assert plan.total_files == 4
    assert set(plan.groups.keys()) == {"Images", "Documents", "Code"}
    assert [e.name for e in plan.groups["Images"]] == ["a.jpg", "b.png"]


def test_build_plan_ignores_subdirectories(tmp_path):
    d = str(tmp_path)
    _touch(d, "a.jpg")
    os.mkdir(os.path.join(d, "Existing"))
    _touch(os.path.join(d, "Existing"), "nested.pdf")

    plan = build_plan(d)

    assert plan.total_files == 1
    assert set(plan.groups.keys()) == {"Images"}


def test_build_plan_rejects_non_directory(tmp_path):
    missing = str(tmp_path / "nope")
    with pytest.raises(NotADirectoryError):
        build_plan(missing)


def test_apply_plan_dry_run_moves_nothing(tmp_path):
    d = str(tmp_path)
    _touch(d, "a.jpg")
    plan = build_plan(d)

    moves = apply_plan(d, plan, dry_run=True)

    assert len(moves) == 1
    assert os.path.exists(os.path.join(d, "a.jpg"))
    assert not os.path.exists(os.path.join(d, "Images"))


def test_apply_plan_moves_files_into_category_folders(tmp_path):
    d = str(tmp_path)
    _touch(d, "a.jpg")
    _touch(d, "b.pdf")
    plan = build_plan(d)

    moves = apply_plan(d, plan, dry_run=False)

    assert len(moves) == 2
    assert os.path.exists(os.path.join(d, "Images", "a.jpg"))
    assert os.path.exists(os.path.join(d, "Documents", "b.pdf"))
    assert not os.path.exists(os.path.join(d, "a.jpg"))


def test_build_plan_recursive_collects_nested_files(tmp_path):
    d = str(tmp_path)
    _touch(d, "top.jpg")
    os.makedirs(os.path.join(d, "sub", "deep"))
    _touch(os.path.join(d, "sub"), "nested.pdf")
    _touch(os.path.join(d, "sub", "deep"), "deeper.py")

    non_recursive = build_plan(d, recursive=False)
    assert non_recursive.total_files == 1

    recursive = build_plan(d, recursive=True)
    assert recursive.total_files == 3
    names = {e.name for entries in recursive.groups.values() for e in entries}
    assert os.path.join("sub", "nested.pdf") in names
    assert os.path.join("sub", "deep", "deeper.py") in names


def test_recursive_apply_flattens_into_top_level_categories(tmp_path):
    d = str(tmp_path)
    os.makedirs(os.path.join(d, "sub"))
    _touch(os.path.join(d, "sub"), "photo.jpg")

    plan = build_plan(d, recursive=True)
    apply_plan(d, plan, dry_run=False)

    assert os.path.exists(os.path.join(d, "Images", "photo.jpg"))
    assert not os.path.exists(os.path.join(d, "sub", "photo.jpg"))


def test_recursive_is_idempotent_and_skips_category_dirs(tmp_path):
    d = str(tmp_path)
    _touch(d, "a.jpg")
    apply_plan(d, build_plan(d, recursive=True), dry_run=False)

    # A second recursive pass must not re-collect the already-sorted file.
    second = build_plan(d, recursive=True)
    assert second.total_files == 0


def test_apply_plan_resolves_filename_collisions(tmp_path):
    d = str(tmp_path)
    os.makedirs(os.path.join(d, "one"))
    os.makedirs(os.path.join(d, "two"))
    _touch(os.path.join(d, "one"), "report.pdf", "first")
    _touch(os.path.join(d, "two"), "report.pdf", "second")

    plan = build_plan(d, recursive=True)
    moves = apply_plan(d, plan, dry_run=False)

    assert len(moves) == 2
    docs = sorted(os.listdir(os.path.join(d, "Documents")))
    assert docs == ["report (1).pdf", "report.pdf"]
