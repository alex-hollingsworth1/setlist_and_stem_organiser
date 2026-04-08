"""Command-line interface for classifying and organising stem exports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .classifier import CATEGORY_KEYWORDS
from .models import PlannedAction
from .organiser import execute_plan
from .planner import plan_organisation
from .config import load_keyword_overrides, build_effective_keywords


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
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print category counts"
        )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to JSON config file with extra keyword mappings.",
    )
    parser.add_argument(
        "--show-other",
        action="store_true",
        help="Print files in OTHER category"
    )

    return parser


def _print_actions(actions: list[PlannedAction]) -> None:
    for action in actions:
        line = f"{action.source.name} -> [{action.category.value}]"
        print(line)

def _print_category_summary(actions: list[PlannedAction]) -> None:
    counts = {}

    for action in actions:
        category = action.category
        counts[category] = counts.get(category, 0) + 1

    for category, count in counts.items():
        print(f"{category.value}: {count}")

def show_other_files(actions: list[PlannedAction]) -> int:
    total = 0
    for action in actions:
        if action.category.value == "OTHER":
            line = f"{action.source.name}"
            print(line)
            total += 1
    
    return total
    



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
    summary_only: bool = args.summary_only
    show_other: bool = args.show_other
    config_path: Path | None = args.config

    keywords = None
    if config_path:
        config_keywords = load_keyword_overrides(config_path)
        keywords = build_effective_keywords(defaults=CATEGORY_KEYWORDS, overrides=config_keywords)

    try:
        actions = plan_organisation(source_dir, output_root, keywords=keywords)
    except NotADirectoryError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not actions:
        print("No audio files found in source directory.", file=sys.stderr)
        return 0

    if not quiet and not summary_only and not show_other:
        _print_actions(actions)

    if summary_only:
        _print_category_summary(actions)

    if show_other:
        print("OTHER:")
        total = show_other_files(actions)
        print(f"{total} files")

    try:
        report = execute_plan(actions, dry_run=dry_run)
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not quiet and not show_other:
            mode = "Dry-run" if report.dry_run else "Copied"
            print(f"{mode}: {report.copied_files} file(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
