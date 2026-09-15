"""Command-line interface for the smart file sorter."""

from __future__ import annotations

import argparse
import sys

from .sorter import build_plan, apply_plan


def _format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="smart-sort",
        description="Organize a directory's files into category subfolders.",
    )
    parser.add_argument("directory", help="Directory whose top-level files should be sorted")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move files (default is a dry-run preview)",
    )
    args = parser.parse_args(argv)

    try:
        plan = build_plan(args.directory)
    except NotADirectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if plan.total_files == 0:
        print("No files to sort.")
        return 0

    print(f"Plan for {args.directory} ({plan.total_files} files):")
    for category, entries in plan.groups.items():
        total = sum(e.size_bytes for e in entries)
        print(f"  {category}/  ({len(entries)} files, {_format_size(total)})")
        for entry in entries:
            print(f"    - {entry.name}")

    moves = apply_plan(args.directory, plan, dry_run=not args.apply)
    if args.apply:
        print(f"\nMoved {len(moves)} files into category folders.")
    else:
        print("\nDry run complete. Re-run with --apply to move the files.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
