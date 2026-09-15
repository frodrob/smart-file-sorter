"""Core sorting logic: turn a list of files into a category-based plan and apply it."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field, asdict
from typing import Iterable

from .categories import category_for


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


def build_plan(directory: str) -> SortPlan:
    """Scan ``directory`` and build a :class:`SortPlan` grouping files by category.

    Only top-level files are considered; existing subdirectories (for example
    category folders created by a previous run) are left untouched.
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"{directory!r} is not a directory")

    groups: dict[str, list[FileEntry]] = {}
    for name in _iter_files(directory):
        category = category_for(name)
        size = os.path.getsize(os.path.join(directory, name))
        groups.setdefault(category, []).append(
            FileEntry(name=name, category=category, size_bytes=size)
        )

    # Sort category keys for stable, predictable output.
    ordered = {key: groups[key] for key in sorted(groups)}
    return SortPlan(groups=ordered)


def apply_plan(directory: str, plan: SortPlan, *, dry_run: bool = False) -> list[dict]:
    """Move files described by ``plan`` into ``<directory>/<Category>/`` folders.

    Returns a list of ``{"from", "to", "category"}`` records describing each move.
    When ``dry_run`` is true the moves are computed but not performed.
    """
    moves: list[dict] = []
    for category, entries in plan.groups.items():
        target_dir = os.path.join(directory, category)
        for entry in entries:
            source = os.path.join(directory, entry.name)
            destination = os.path.join(target_dir, entry.name)
            moves.append({"from": entry.name, "to": os.path.join(category, entry.name), "category": category})
            if dry_run:
                continue
            os.makedirs(target_dir, exist_ok=True)
            shutil.move(source, destination)
    return moves
