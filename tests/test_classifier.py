from pathlib import Path

from setlist_organiser.classifier import classify_name, classify_path
from setlist_organiser.models import Category


def test_classify_direct_hits_for_each_category() -> None:
    cases = {
        "song_perc_shaker.wav": Category.PERC,
        "song_drum_kit.wav": Category.DRUMS,
        "song_bass.wav": Category.BASS,
        "song_sub_808.wav": Category.SUB,
        "song_keys_piano.wav": Category.KEYS,
        "song_lead_gtr.wav": Category.GTR,
        "song_vox_lead.wav": Category.VOX,
        "song_bvs_stack.wav": Category.BVS,
        "song_fx_riser.wav": Category.FX,
        "song_click.wav": Category.CLICK,
        "song_cues_talkback.wav": Category.CUES,
        "song_strings_violin": Category.STRINGS,
        "song_brass_trumpet": Category.BRASS,
        "song_woodwind_flute": Category.WOODWIND
    }

    for name, expected in cases.items():
        classified = classify_name(name)
        assert classified.category == expected
        assert classified.matched_keyword is not None


def test_classify_aliases_and_abbreviations() -> None:
    assert classify_name("Bridge_gtr_take.wav").category == Category.GTR
    assert classify_name("Choir_bvs_stem.wav").category == Category.BVS
    assert classify_name("Scene_fx_hit.wav").category == Category.FX
    assert classify_name("countin_reference.wav").category == Category.CUES


def test_classify_ambiguous_filename_resolves_by_priority() -> None:
    # VOX wins over FX by current resolver priority.
    assert classify_name("intro_vox_fx.wav").category == Category.VOX
    # DRUMS wins over PERC by current resolver priority.
    assert classify_name("section_drums_perc.wav").category == Category.DRUMS


def test_classify_no_match_falls_back_to_other() -> None:
    classified = classify_name("session_print_master.wav")
    assert classified.category == Category.OTHER
    assert classified.matched_keyword is None


def test_classify_path_keeps_original_source_path() -> None:
    source = Path("/tmp/stems/chorus_vox.wav")
    classified = classify_path(source)
    assert classified.source == source
