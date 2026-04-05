"""Command-line interface for classifying and organising stem exports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import PlannedAction, Category
from .organiser import execute_plan
from .planner import plan_organisation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan SOURCE_DIR (non-recursive) for audio stems, classify by filename, "
            "and copy into OUTPUT_ROOT/<CATEGORY>/."
        )
    )
    parser.add_argument(
        "source_dir",
        type=Path,
        metavar="SOURCE_DIR",
        help="Directory containing stem files (not scanned recursively).",
    )
    parser.add_argument(
        "output_root",
        type=Path,
        metavar="OUTPUT_ROOT",
        help="Root directory for category subfolders (created as needed).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned operations without creating directories or copying files.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the summary line (no per-file listing).",
    )

    # parser.add_argument(
    #     "--summary-only",
    #     help="Print category counts"
    #     )
    return parser


def _print_actions(actions: list[PlannedAction]) -> None:
    for action in actions:
        line = f"{action.source} -> {action.destination} [{action.category.value}]"
        print(line)

# def _print_categories(categories) -> None:
#     total = len(categories)    
#     print(f"The total number of categories is {total}.")



def main(argv: list[str] | None = None) -> int:
    """
    Run the CLI. Exit codes: 0 success, 1 error (bad paths, I/O failure).

    When ``argv`` is None, uses ``sys.argv[1:]``.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    source_dir: Path = args.source_dir
    output_root: Path = args.output_root
    dry_run: bool = args.dry_run
    quiet: bool = args.quiet

    try:
        actions = plan_organisation(source_dir, output_root)
    except NotADirectoryError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not actions:
        print("No audio files found in source directory.", file=sys.stderr)
        return 0

    if not quiet:
        _print_actions(actions)

    try:
        report = execute_plan(actions, dry_run=dry_run)
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 1

    mode = "Dry-run" if report.dry_run else "Copied"
    print(f"{mode}: {report.copied_files} file(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
