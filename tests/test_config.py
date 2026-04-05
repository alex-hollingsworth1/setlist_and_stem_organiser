from pathlib import Path
from setlist_organiser.models import Category
from setlist_organiser.cli import build_effective_keywords

def test_load_keyword_overrides(tmp_path: Path) -> None:
    config_file = tmp_path / "test_config.json"
    config_file.write_text('{"keywords": {"DRUMS": ["room", "hh"]}}')

    assert {Category.DRUMS: ("room", "hh")}

def test_build_effective_keywords() -> None:
    default_dict = {Category.DRUMS: ("kick", "snare")}
    override_dict = {Category.DRUMS: ("thud", "stomps")}

    result = build_effective_keywords(defaults=default_dict, overrides=override_dict)
    assert result == {Category.DRUMS: ("kick", "snare", "thud", "stomps")}