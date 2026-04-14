from pathlib import Path
import pytest

from setlist_organiser.cli import build_parser, main


def test_build_parser_accepts_required_args() -> None:
    parser = build_parser()
    args = parser.parse_args(["source_folder", "output_folder"])
    
    assert args.source_dir == Path("source_folder")
    assert args.output_root == Path("output_folder")
    assert args.dry_run is False
    assert args.numbered is False

def test_build_parser_accepts_optional_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["source_folder", "output_folder", "--dry-run", "--numbered"])
    
    assert args.dry_run is True
    assert args.numbered is True

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
