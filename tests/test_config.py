from pathlib import Path

from setlist_organiser.config import (
    build_effective_keywords,
    load_keyword_overrides,
    merge_keywords_into_stored_overrides,
)
from setlist_organiser.models import Category

def test_load_keyword_overrides(tmp_path: Path) -> None:
    config_file = tmp_path / "test_config.json"
    config_file.write_text('{"keywords": {"DRUMS": ["room", "hh"]}}')

    result = load_keyword_overrides(config_file)
    assert result == {Category.DRUMS: ("room", "hh")}

def test_build_effective_keywords() -> None:
    default_dict = {Category.DRUMS: ("kick", "snare")}
    override_dict = {Category.DRUMS: ("thud", "stomps")}

    result = build_effective_keywords(defaults=default_dict, overrides=override_dict)
    assert result == {Category.DRUMS: ("kick", "snare", "thud", "stomps")}


def test_merge_keywords_into_stored_overrides_creates_file(tmp_path: Path) -> None:
    path = tmp_path / "kw.json"
    assert not path.exists()
    merge_keywords_into_stored_overrides(path, Category.GTR, ("custom", "extra"))
    assert path.exists()
    loaded = load_keyword_overrides(path)
    assert loaded == {Category.GTR: ("custom", "extra")}


def test_merge_keywords_into_stored_overrides_appends_and_dedupes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "kw.json"
    path.write_text('{"keywords": {"GTR": ["first"], "DRUMS": ["pocket"]}}')
    merge_keywords_into_stored_overrides(
        path, Category.GTR, ("second", "FIRST", "first")
    )
    loaded = load_keyword_overrides(path)
    assert loaded[Category.DRUMS] == ("pocket",)
    # "FIRST" / "first" de-dupe against existing "first" (case-insensitive)
    assert loaded[Category.GTR] == ("first", "second")
    merged = build_effective_keywords(
        {Category.GTR: ("gtr",), Category.DRUMS: ("kick",)},
        loaded,
    )
    assert merged[Category.GTR] == ("gtr", "first", "second")
    assert merged[Category.DRUMS] == ("kick", "pocket")