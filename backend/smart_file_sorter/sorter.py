"""Core sorting logic: turn a list of files into a category-based plan and apply it."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field, asdict
from typing import Iterable

from .categories import CATEGORIES, FALLBACK_CATEGORY, category_for

# Top-level folder names produced by :func:`apply_plan`. Recursive scans skip
# these so already-sorted files are never re-collected.
CATEGORY_DIRS: set[str] = set(CATEGORIES.keys()) | {FALLBACK_CATEGORY}


@dataclass(frozen=True)
class FileEntry:
    """A single file discovered in the source directory."""

    name: str
    category: str
    size_bytes: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SortPlan:
    """A proposed reorganization grouping files by target category folder."""

    groups: dict[str, list[FileEntry]] = field(default_factory=dict)

    @property
    def total_files(self) -> int:
        return sum(len(entries) for entries in self.groups.values())

    def to_dict(self) -> dict:
        return {
            "total_files": self.total_files,
            "groups": {
                category: [entry.to_dict() for entry in entries]
                for category, entries in self.groups.items()
            },
        }


def _iter_files(directory: str) -> Iterable[str]:
    """Yield names of regular files directly inside ``directory`` (non-recursive)."""
    for name in sorted(os.listdir(directory)):
        full = os.path.join(directory, name)
        if os.path.isfile(full):
            yield name


def _iter_files_recursive(directory: str) -> Iterable[str]:
    """Yield paths (relative to ``directory``) of files at any depth.

    Existing top-level category folders are skipped so previously sorted files
    are not re-collected, keeping repeated runs idempotent.
    """
    results: list[str] = []
    base = os.path.abspath(directory)
    for root, dirs, files in os.walk(directory):
        if os.path.abspath(root) == base:
            dirs[:] = [d for d in dirs if d not in CATEGORY_DIRS]
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            results.append(os.path.relpath(full, directory))
    return results


def build_plan(directory: str, *, recursive: bool = False) -> SortPlan:
    """Scan ``directory`` and build a :class:`SortPlan` grouping files by category.

    By default only top-level files are considered. With ``recursive=True`` files
    inside subfolders are also collected (their entry ``name`` is the path relative
    to ``directory``). Existing top-level category folders are always left
    untouched so repeated runs are idempotent.
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"{directory!r} is not a directory")

    names = _iter_files_recursive(directory) if recursive else _iter_files(directory)

    groups: dict[str, list[FileEntry]] = {}
    for name in names:
        category = category_for(name)
        size = os.path.getsize(os.path.join(directory, name))
        groups.setdefault(category, []).append(
            FileEntry(name=name, category=category, size_bytes=size)
        )

    # Sort category keys for stable, predictable output.
    ordered = {key: groups[key] for key in sorted(groups)}
    return SortPlan(groups=ordered)


def _unique_destination(target_dir: str, base: str, reserved: set[str]) -> str:
    """Pick a filename in ``target_dir`` that collides with neither an existing
    file nor a name already claimed in this run, appending ``" (n)"`` if needed."""
    candidate = base
    stem, ext = os.path.splitext(base)
    counter = 1
    while candidate in reserved or os.path.exists(os.path.join(target_dir, candidate)):
        candidate = f"{stem} ({counter}){ext}"
        counter += 1
    reserved.add(candidate)
    return candidate


def apply_plan(directory: str, plan: SortPlan, *, dry_run: bool = False) -> list[dict]:
    """Move files described by ``plan`` into ``<directory>/<Category>/`` folders.

    Returns a list of ``{"from", "to", "category"}`` records describing each move.
    Filename collisions (common with recursive scans) are resolved by appending
    ``" (n)"`` to the target name. When ``dry_run`` is true the moves are computed
    but nothing is written to disk.
    """
    moves: list[dict] = []
    reserved_by_dir: dict[str, set[str]] = {}
    for category, entries in plan.groups.items():
        target_dir = os.path.join(directory, category)
        reserved = reserved_by_dir.setdefault(target_dir, set())
        for entry in entries:
            source = os.path.join(directory, entry.name)
            base = os.path.basename(entry.name)
            final_base = _unique_destination(target_dir, base, reserved)
            destination = os.path.join(target_dir, final_base)
            moves.append(
                {
                    "from": entry.name,
                    "to": os.path.join(category, final_base),
                    "category": category,
                }
            )
            if dry_run:
                continue
            os.makedirs(target_dir, exist_ok=True)
            shutil.move(source, destination)
    return moves
