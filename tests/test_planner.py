"""Tests for planner module."""

from pathlib import Path

import pytest

from setlist_organiser.models import Category
from setlist_organiser.planner import (
    _allocate_unique_destination,
    plan_organisation,
)


def test_plan_organisation_happy_path(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    out = tmp_path / "out"
    (source / "song_keys_piano.wav").write_bytes(b"")
    (source / "song_bass.wav").write_bytes(b"")

    actions = plan_organisation(source, out)
    assert len(actions) == 2
    by_source = {a.source.name: a for a in actions}
    assert by_source["song_keys_piano.wav"].category == Category.KEYS
    assert by_source["song_keys_piano.wav"].destination == out / "KEYS" / "song_keys_piano.wav"
    assert by_source["song_bass.wav"].category == Category.BASS
    assert by_source["song_bass.wav"].destination == out / "BASS" / "song_bass.wav"
    ordered = sorted(a.source.as_posix() for a in actions)
    assert [a.source.as_posix() for a in actions] == ordered


def test_plan_organisation_skips_non_audio(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    (source / "stem.wav").write_bytes(b"")
    (source / "readme.txt").write_text("x", encoding="utf-8")
    (source / ".hidden.wav").write_bytes(b"")

    actions = plan_organisation(source, tmp_path / "out")
    assert len(actions) == 1
    assert actions[0].source.name == "stem.wav"


def test_plan_organisation_raises_when_source_not_directory(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        plan_organisation(f, tmp_path / "out")


def test_allocate_unique_destination_suffixes_on_collision(tmp_path: Path) -> None:
    """Flat exports rarely collide; suffix logic covers same dest from multiple sources."""
    used: set[Path] = set()
    base = tmp_path / "KEYS" / "dup.wav"
    first = _allocate_unique_destination(base, used)
    second = _allocate_unique_destination(base, used)
    third = _allocate_unique_destination(base, used)
    assert first == tmp_path / "KEYS" / "dup.wav"
    assert second == tmp_path / "KEYS" / "dup_2.wav"
    assert third == tmp_path / "KEYS" / "dup_3.wav"
