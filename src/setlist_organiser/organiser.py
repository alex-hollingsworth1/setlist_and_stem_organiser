"""Execute planned stem copies (or preview them without touching disk)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .models import PlannedAction, RunReport


def output_folder_for_reveal(actions: list[PlannedAction]) -> Path | None:
    """
    Directory that should be opened in Finder for a completed batch: common
    ancestor of all destinations, or the parent when that path is a file.
    Returns None if the folder cannot be determined or does not exist.
    """
    if not actions:
        return None
    try:
        dest_paths = [a.destination.resolve() for a in actions]
    except OSError:
        return None
    try:
        common = Path(os.path.commonpath([str(p) for p in dest_paths]))
        if common.suffix:  # commonpath was a file path
            folder = common.parent
        else:
            folder = common
    except ValueError:
        folder = dest_paths[0].parent
    if not folder.is_dir():
        return None
    return folder


def _reveal_output_in_finder(actions: list[PlannedAction]) -> None:
    """
    On macOS, open a Finder window for the output location (``open``).

    See :func:`output_folder_for_reveal` for which folder is used. No-op on
    other platforms or if anything fails.
    """
    if sys.platform != "darwin" or not actions:
        return
    folder = output_folder_for_reveal(actions)
    if folder is None:
        return
    subprocess.run(
        ["open", str(folder)],
        check=False,
        capture_output=True,
    )


def execute_plan(
    actions: list[PlannedAction],
    *,
    dry_run: bool,
    move: bool = False,
    reveal_in_finder: bool = False,
) -> RunReport:
    """
    Run each planned copy, or preview it.

    When ``dry_run`` is True, no directories are created and no files are copied.
    ``copied_files`` is still set to the number of operations that *would* run
    (same as ``total_files``) so callers can show a consistent summary.

    When ``dry_run`` is False, parent directories are created as needed and each
    source file is copied with :func:`shutil.copy2` (metadata preserved).

    When ``reveal_in_finder`` is True, after a successful run on macOS, opens a
    Finder window on the output folder (see :func:`_reveal_output_in_finder`).
    Ignored when ``dry_run`` is True, or on non-macOS.
    """
    total = len(actions)
    if dry_run:
        return RunReport(
            total_files=total,
            copied_files=total,
            dry_run=True,
        )

    copied = 0

    if move:
        for action in actions:
            _move_one(action)
            copied += 1
    else:
        for action in actions:
            _copy_one(action)
            copied += 1

    if reveal_in_finder:
        _reveal_output_in_finder(actions)

    return RunReport(
        total_files=total,
        copied_files=copied,
        dry_run=False,
    )


def _copy_one(action: PlannedAction) -> None:
    destination_parent = action.destination.parent
    destination_parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(action.source, action.destination)

def _move_one(action: PlannedAction) -> None:
    destination_parent = action.destination.parent
    destination_parent.mkdir(parents=True, exist_ok=True)
    shutil.move(action.source, action.destination)
