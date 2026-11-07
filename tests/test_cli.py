from pathlib import Path
import wave

import pytest
from lxml import etree

from setlist_organiser.cli import build_parser, main


def _write_wav(path: Path, duration_seconds: float = 0.05) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    n_frames = int(sample_rate * duration_seconds)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_frames)


def test_build_parser_accepts_required_args() -> None:
    parser = build_parser()
    args = parser.parse_args(["source_folder", "output_folder"])
    
    assert args.source_dir == Path("source_folder")
    assert args.output_root == Path("output_folder")
    assert args.dry_run is False
    assert args.numbered is False
    assert args.build_session is None

def test_build_parser_accepts_optional_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "source_folder",
            "output_folder",
            "--dry-run",
            "--numbered",
            "--build-session",
            "out/session.als",
        ]
    )
    
    assert args.dry_run is True
    assert args.numbered is True
    assert args.build_session == Path("out/session.als")

def test_build_parser_accepts_config_flag(tmp_path: Path) -> None:
    config_file = tmp_path / "test_config.json"
    config_file.write_text('{"keywords": {}}')
    
    parser = build_parser()
    args = parser.parse_args(["source", "output", "--config", str(config_file)])
    
    assert args.config == config_file

def test_build_parser_fails_without_required_args() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])

# Integration tests

def test_main_dry_run_returns_zero(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    (source / "kick.wav").write_bytes(b"")
    output = tmp_path / "out"
    
    result = main([str(source), str(output), "--dry-run"])
    
    assert result == 0

def test_main_missing_config_returns_one(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    (source / "kick.wav").write_bytes(b"")
    output = tmp_path / "out"
    
    result = main([str(source), str(output), "--config", "nonexistent.json"])
    
    assert result == 1

def test_main_malformed_json_returns_one(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    (source / "kick.wav").write_bytes(b"")
    output = tmp_path / "out"
    
    config_file = tmp_path / "bad.json"
    config_file.write_text("{this is not valid json")
    
    result = main([str(source), str(output), "--config", str(config_file)])
    
    assert result == 1


def test_main_build_session_writes_als(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    _write_wav(source / "kick.wav")
    _write_wav(source / "bass.wav")
    output = tmp_path / "out"
    session_path = tmp_path / "ABLETON" / "session.als"

    result = main(
        [str(source), str(output), "--build-session", str(session_path), "--quiet"]
    )

    assert result == 0
    assert session_path.is_file()
    assert (output / "DRUMS" / "kick.wav").is_file()
    assert (output / "BASS" / "bass.wav").is_file()
    tree = etree.parse(str(session_path))
    localnames = {etree.QName(el).localname for el in tree.iter()}
    assert "AudioTrack" in localnames
    assert "GroupTrack" in localnames


def test_main_build_session_skipped_on_dry_run(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    _write_wav(source / "kick.wav")
    output = tmp_path / "out"
    session_path = tmp_path / "session.als"

    result = main(
        [
            str(source),
            str(output),
            "--dry-run",
            "--build-session",
            str(session_path),
            "--quiet",
        ]
    )

    assert result == 0
    assert not session_path.exists()
    assert not (output / "DRUMS" / "kick.wav").exists()
