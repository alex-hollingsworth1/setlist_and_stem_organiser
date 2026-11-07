from pathlib import Path
from unittest.mock import patch

from setlist_organiser.models import Category, PlannedAction
from setlist_organiser.tempo import (
    TempoEstimate,
    _choose_near_reference,
    _consensus_bpm,
    _normalise_bpm,
    estimate_tempo,
)


def test_normalise_bpm_folds_half_and_double_into_range() -> None:
    assert _normalise_bpm(30.0) == 60.0
    assert _normalise_bpm(240.0) == 120.0
    assert _normalise_bpm(128.4) == 128.4
    assert _normalise_bpm(0.0) is None


def test_choose_near_reference_prefers_half_when_closer() -> None:
    assert _choose_near_reference(240.0, reference_bpm=118.0) == 120.0


def test_consensus_requires_agreement_for_high_confidence() -> None:
    agreed = _consensus_bpm([120.0, 120.5, 119.5])
    assert agreed is not None
    bpm, confidence = agreed
    assert abs(bpm - 120.0) < 1.0
    assert confidence >= 0.5

    single = _consensus_bpm([128.0])
    assert single is not None
    single_bpm, single_confidence = single
    assert single_bpm == 128.0
    assert single_confidence == 0.55


def test_estimate_tempo_returns_none_without_usable_files(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.wav"
    actions = [
        PlannedAction(
            source=missing,
            destination=tmp_path / "DRUMS" / "missing.wav",
            category=Category.DRUMS,
        )
    ]
    with patch("setlist_organiser.tempo.estimate_file_bpm", return_value=None):
        assert estimate_tempo(actions) is None


def test_estimate_tempo_prefers_click_and_applies_consensus(
    tmp_path: Path,
) -> None:
    click = tmp_path / "click.wav"
    kick = tmp_path / "kick.wav"
    pad = tmp_path / "pad.wav"
    actions = [
        PlannedAction(
            source=pad,
            destination=tmp_path / "KEYS" / "pad.wav",
            category=Category.KEYS,
        ),
        PlannedAction(
            source=kick,
            destination=tmp_path / "DRUMS" / "kick.wav",
            category=Category.DRUMS,
        ),
        PlannedAction(
            source=click,
            destination=tmp_path / "CLICK" / "click.wav",
            category=Category.CLICK,
        ),
    ]

    def fake_bpm(path: Path) -> float | None:
        return {
            click: 120.0,
            kick: 120.5,
            pad: 90.0,
        }.get(path)

    with patch("setlist_organiser.tempo.estimate_file_bpm", side_effect=fake_bpm):
        estimate = estimate_tempo(actions, reference_bpm=120.0)

    assert isinstance(estimate, TempoEstimate)
    assert abs(estimate.bpm - 120.0) <= 1.0
    assert estimate.confidence >= 0.5
    assert "click.wav" in estimate.source
    assert "pad.wav" not in estimate.source
