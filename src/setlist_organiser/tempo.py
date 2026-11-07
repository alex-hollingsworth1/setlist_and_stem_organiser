"""Tempo estimation from stem audio for Ableton session metadata."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median

import librosa
import numpy as np

from .models import Category, PlannedAction

_MIN_BPM = 60.0
_MAX_BPM = 200.0
_AGREE_TOLERANCE_BPM = 2.0
_MAX_FILES_PER_CATEGORY = 3
_MAX_LOAD_SECONDS = 60.0

_PREFERRED_CATEGORIES: tuple[Category, ...] = (
    Category.CLICK,
    Category.DRUMS,
    Category.PERC,
)


@dataclass(frozen=True, slots=True)
class TempoEstimate:
    """Accepted tempo estimate for writing into a session."""

    bpm: float
    confidence: float
    source: str


def _normalise_bpm(raw: float | np.ndarray | np.floating) -> float | None:
    value = float(np.atleast_1d(raw)[0])
    if not np.isfinite(value) or value <= 0:
        return None
    while value < _MIN_BPM and value * 2 <= _MAX_BPM:
        value *= 2
    while value > _MAX_BPM and value / 2 >= _MIN_BPM:
        value /= 2
    if value < _MIN_BPM or value > _MAX_BPM:
        return None
    return round(value, 1)


def _choose_near_reference(
    bpm: float, reference_bpm: float | None
) -> float:
    """Prefer bpm, bpm/2, or bpm*2 closest to the template/reference tempo."""
    candidates = [bpm]
    half = bpm / 2
    double = bpm * 2
    if _MIN_BPM <= half <= _MAX_BPM:
        candidates.append(round(half, 1))
    if _MIN_BPM <= double <= _MAX_BPM:
        candidates.append(round(double, 1))
    if reference_bpm is None:
        return bpm
    return min(candidates, key=lambda value: abs(value - reference_bpm))


def estimate_file_bpm(path: Path) -> float | None:
    """Estimate BPM for a single audio file. Returns None on failure."""
    try:
        y, sr = librosa.load(
            str(path),
            sr=None,
            mono=True,
            duration=_MAX_LOAD_SECONDS,
        )
    except Exception:
        return None
    if y.size == 0 or sr <= 0:
        return None
    try:
        tempo, _beats = librosa.beat.beat_track(y=y, sr=sr)
    except Exception:
        return None
    return _normalise_bpm(tempo)


def _candidate_actions(actions: list[PlannedAction]) -> list[PlannedAction]:
    by_category: dict[Category, list[PlannedAction]] = defaultdict(list)
    for action in actions:
        by_category[action.category].append(action)

    selected: list[PlannedAction] = []
    for category in _PREFERRED_CATEGORIES:
        selected.extend(by_category.get(category, [])[:_MAX_FILES_PER_CATEGORY])
    if selected:
        return selected

    # Fallback: first few stems of any category.
    return list(actions)[:_MAX_FILES_PER_CATEGORY]


def _consensus_bpm(values: list[float]) -> tuple[float, float] | None:
    """Return (bpm, confidence) when estimates agree enough to trust."""
    if not values:
        return None
    if len(values) == 1:
        return values[0], 0.55

    best_cluster: list[float] = []
    for anchor in values:
        cluster = [v for v in values if abs(v - anchor) <= _AGREE_TOLERANCE_BPM]
        if len(cluster) > len(best_cluster):
            best_cluster = cluster

    if len(best_cluster) >= 2:
        return float(median(best_cluster)), min(0.95, 0.6 + 0.1 * len(best_cluster))

    # No agreement — keep the median but low confidence.
    return float(median(values)), 0.4


def estimate_tempo(
    actions: list[PlannedAction],
    *,
    reference_bpm: float | None = None,
    min_confidence: float = 0.5,
) -> TempoEstimate | None:
    """
    Estimate session tempo from planned stem sources.

    Prefers CLICK / DRUMS / PERC. Returns None when estimates are missing or
    too weak to apply safely.
    """
    candidates = _candidate_actions(actions)
    measured: list[float] = []
    sources: list[str] = []
    for action in candidates:
        bpm = estimate_file_bpm(action.source)
        if bpm is None:
            continue
        adjusted = _choose_near_reference(bpm, reference_bpm)
        measured.append(adjusted)
        sources.append(action.source.name)

    consensus = _consensus_bpm(measured)
    if consensus is None:
        return None
    bpm, confidence = consensus
    if confidence < min_confidence:
        return None

    return TempoEstimate(
        bpm=round(bpm, 1),
        confidence=round(confidence, 2),
        source=", ".join(sources[:5]) or "unknown",
    )
