"""Execute planned stem copies (or preview them without touching disk)."""

from __future__ import annotations

import shutil
from pathlib import Path

from .models import PlannedAction, RunReport


def execute_plan(actions: list[PlannedAction], *, dry_run: bool, move: bool = False) -> RunReport:
    """
    Run each planned copy, or preview it.

    When ``dry_run`` is True, no directories are created and no files are copied.
    ``copied_files`` is still set to the number of operations that *would* run
    (same as ``total_files``) so callers can show a consistent summary.

    When ``dry_run`` is False, parent directories are created as needed and each
    source file is copied with :func:`shutil.copy2` (metadata preserved).
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
