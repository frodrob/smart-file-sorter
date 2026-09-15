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
    parser.add_argument("directory", help="Directory whose files should be sorted")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move files (default is a dry-run preview)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only preview the plan; never move anything (overrides --apply)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Also scan files inside subfolders (not just the top level)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt when applying",
    )
    args = parser.parse_args(argv)

    try:
        plan = build_plan(args.directory, recursive=args.recursive)
    except NotADirectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if plan.total_files == 0:
        print("No files to sort.")
        return 0

    scope = "recursively" if args.recursive else "at top level"
    print(f"Plan for {args.directory} ({plan.total_files} files, {scope}):")
    for category, entries in plan.groups.items():
        total = sum(e.size_bytes for e in entries)
        print(f"  {category}/  ({len(entries)} files, {_format_size(total)})")
        for entry in entries:
            print(f"    - {entry.name}")

    do_move = args.apply and not args.dry_run
    if not do_move:
        print("\nDry run complete. Re-run with --apply to move the files.")
        return 0

    if not args.yes:
        prompt = (
            f"\nMove {plan.total_files} files into category folders under "
            f"{args.directory}? [y/N] "
        )
        try:
            answer = input(prompt)
        except EOFError:
            answer = ""
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted. No files were moved.")
            return 0

    moves = apply_plan(args.directory, plan, dry_run=False)
    print(f"\nMoved {len(moves)} files into category folders.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
