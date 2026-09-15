import os

from smart_file_sorter.cli import main


def _touch(directory, name, content="x"):
    with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
        handle.write(content)


def test_cli_dry_run_default_moves_nothing(tmp_path, capsys):
    d = str(tmp_path)
    _touch(d, "a.jpg")

    rc = main([d])

    assert rc == 0
    assert "Dry run complete" in capsys.readouterr().out
    assert os.path.exists(os.path.join(d, "a.jpg"))
    assert not os.path.exists(os.path.join(d, "Images"))


def test_cli_apply_with_yes_moves_files(tmp_path, capsys):
    d = str(tmp_path)
    _touch(d, "a.jpg")

    rc = main([d, "--apply", "--yes"])

    assert rc == 0
    assert "Moved 1 files" in capsys.readouterr().out
    assert os.path.exists(os.path.join(d, "Images", "a.jpg"))


def test_cli_dry_run_flag_overrides_apply(tmp_path, capsys):
    d = str(tmp_path)
    _touch(d, "a.jpg")

    rc = main([d, "--apply", "--dry-run"])

    assert rc == 0
    assert "Dry run complete" in capsys.readouterr().out
    assert not os.path.exists(os.path.join(d, "Images"))


def test_cli_apply_aborts_when_declined(tmp_path, capsys, monkeypatch):
    d = str(tmp_path)
    _touch(d, "a.jpg")
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")

    rc = main([d, "--apply"])

    assert rc == 0
    assert "Aborted" in capsys.readouterr().out
    assert os.path.exists(os.path.join(d, "a.jpg"))


def test_cli_recursive_apply(tmp_path, capsys):
    d = str(tmp_path)
    os.makedirs(os.path.join(d, "sub"))
    _touch(os.path.join(d, "sub"), "nested.pdf")

    rc = main([d, "--recursive", "--apply", "--yes"])

    assert rc == 0
    assert os.path.exists(os.path.join(d, "Documents", "nested.pdf"))


def test_cli_errors_on_missing_directory(tmp_path, capsys):
    rc = main([str(tmp_path / "nope")])

    assert rc == 2
    assert "error:" in capsys.readouterr().err
