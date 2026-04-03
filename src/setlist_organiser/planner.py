"""Plan copy operations for organising stems by category."""

from __future__ import annotations

from pathlib import Path

from .classifier import classify_path
from .models import PlannedAction

_AUDIO_SUFFIXES: frozenset[str] = frozenset(
    {
        ".wav",
        ".wave",
        ".aif",
        ".aiff",
        ".flac",
        ".mp3",
        ".m4a",
        ".ogg",
    }
)


def _is_audio_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.name.startswith("."):
        return False
    return path.suffix.lower() in _AUDIO_SUFFIXES


def _allocate_unique_destination(dest: Path, used: set[Path]) -> Path:
    """Pick a destination path, suffixing stem (_2, _3, ...) on collision."""
    if dest not in used:
        used.add(dest)
        return dest
    parent = dest.parent
    stem = dest.stem
    suffix = dest.suffix
    n = 2
    while True:
        candidate = parent / f"{stem}_{n}{suffix}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        n += 1


def plan_organisation(source_dir: Path, output_root: Path) -> list[PlannedAction]:
    """
    Scan ``source_dir`` (non-recursive) for audio files, classify each stem,
    and return planned copy destinations under ``output_root / <CATEGORY> /``.
    """
    resolved_source = source_dir.resolve()
    if not resolved_source.is_dir():
        msg = f"Source is not a directory: {source_dir}"
        raise NotADirectoryError(msg)

    output_base = output_root.resolve()
    used_destinations: set[Path] = set()
    actions: list[PlannedAction] = []

    for path in sorted(resolved_source.iterdir(), key=lambda p: p.as_posix()):
        if not _is_audio_file(path):
            continue
        classified = classify_path(path)
        category = classified.category
        base_dest = output_base / category.value / path.name
        dest = _allocate_unique_destination(base_dest, used_destinations)
        actions.append(
            PlannedAction(source=path, destination=dest, category=category)
        )

    actions.sort(key=lambda a: a.source.as_posix())
    return actions
