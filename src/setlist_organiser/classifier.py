"""Filename classification logic for setlist organiser."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .models import Category, ClassifiedFile

_SEPARATOR_RE = re.compile(r"[^a-z0-9]+")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class _CategoryMatch:
    """Internal match candidate for potential category resolution."""

    category: Category
    matched_keyword: str


CATEGORY_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.PERC: (
        "perc",
        "percussion",
        "shaker",
        "tambourine",
        "tamb",
        "conga",
        "congas",
        "bongo",
        "bongos",
        "clap",
        "claps",
        "stomp",
        "stomps",
        "bells",
        "triangle",
        "hit",
        "hits",
    ),
    Category.DRUMS: (
        "drum",
        "drums",
        "kit",
        "snare",
        "snares",
        "snr",
        "kick",
        "kicks",
        "kck",
        "kik",
        "toms",
        "hihat",
        "hi hat",
        "hh",
        "cym",
        "ride",
        "crash",
        "overhead",
        "oh",
        "rimshot",
        "rim",
    ),
    Category.BASS: (
        "bass",
        "bassgtr",
        "bass guitar",
    ),
    Category.SUB: (
        "sub",
        "808",
        "low end",
        "sub bass",
    ),
    Category.KEYS: (
        "keys",
        "key",
        "piano",
        "rhodes",
        "wurli",
        "organ",
        "synth",
        "pad",
        "arp",
        "synths",
        "synth pad",
        "sine",
        "saw",
        "square",
        "sc",
        "sidechain"
    ),
    Category.GTR: (
        "gtr",
        "guitar",
        "acoustic",
        "electric",
        "lead gtr",
        "rhythm gtr",
    ),
    Category.VOX: (
        "vox",
        "voc",
        "vocal",
        "lead vox",
        "lead vocal",
        "vocoder",
        "adlib",
        "adlibs",
        "ad libs",
        "double",
        "dbl",
        "doubles",
        "lv",
    ),
    Category.BVS: (
        "bv",
        "bvs",
        "backing vocal",
        "backing vox",
        "harmony",
        "choir",
        "stack",
        "gang vox",
        "harmonies",
        "harms",
    ),
    Category.FX: (
        "fx",
        "sfx",
        "impact",
        "riser",
        "sweep",
        "transition",
        "verb",
        "reverb",
        "rverb",
        "rvb",
        "delay",
        "dly",
        "throw",
        "beep",
        "noise",
        "white noise",
        "atmos",
        "atmosphere"
    ),
    Category.CLICK: (
        "click",
        "metronome",
        "metro",
        "clk",
    ),
    Category.CUES: (
        "cue",
        "cues",
        "guide",
        "guide vox",
        "guide vocal",
        "talkback",
        "count in",
        "countin",
    ),
    Category.STRINGS: (
        "strings",
        "string",
        "violin",
        "viola",
        "cello",
    ),
    Category.BRASS: (
        "brass",
        "trumpet",
        "trombone",
        "tuba",
        "horn",
        "horns",
    ),
    Category.WOODWIND: (
        "woodwind",
        "flute",
        "oboe",
        "clarinet",
        "saxophone",
        "bassoon",
    ),
    Category.OTHER: (),
}


CATEGORY_PRIORITY: tuple[Category, ...] = (
    Category.CLICK,
    Category.CUES,
    Category.BVS,
    Category.VOX,
    Category.FX,
    Category.DRUMS,
    Category.PERC,
    Category.SUB,
    Category.BASS,
    Category.KEYS,
    Category.GTR,
    Category.STRINGS,
    Category.BRASS,
    Category.WOODWIND,
    Category.OTHER,
)


def _normalize_name(name: str) -> str:
    cleaned = _SEPARATOR_RE.sub(" ", name.lower())
    return _SPACE_RE.sub(" ", cleaned).strip()


def _tokenize(normalized_name: str) -> set[str]:
    if not normalized_name:
        return set()
    return set(normalized_name.split(" "))


def _keyword_matches(
    keyword: str, normalized_name: str, tokens: set[str]
) -> bool:
    normalized_keyword = _normalize_name(keyword)
    if not normalized_keyword:
        return False
    if " " in normalized_keyword:
        return normalized_keyword in normalized_name
    return normalized_keyword in tokens


def _collect_candidate_matches(
    name: str,
    *,
    keywords: dict[Category, tuple[str, ...]],
) -> list[_CategoryMatch]:
    normalized_name = _normalize_name(Path(name).stem)
    tokens = _tokenize(normalized_name)
    candidates: list[_CategoryMatch] = []

    for category, keyword_tuple in keywords.items():
        for keyword in keyword_tuple:
            if _keyword_matches(keyword, normalized_name, tokens):
                candidates.append(
                    _CategoryMatch(category=category, matched_keyword=keyword)
                )
                break

    return candidates


def _resolve_single_category(
    candidates: list[_CategoryMatch],
    *,
    priority: tuple[Category, ...],
) -> _CategoryMatch:
    if not candidates:
        return _CategoryMatch(
            category=Category.OTHER,
            matched_keyword="",
        )

    candidate_by_category = {candidate.category: candidate for candidate in candidates}
    for category in priority:
        if category in candidate_by_category:
            return candidate_by_category[category]

    return _CategoryMatch(category=Category.OTHER, matched_keyword="")


def classify_name(
    name: str,
    source: Path | None = None,
    *,
    keywords: dict[Category, tuple[str, ...]] | None = None,
) -> ClassifiedFile:
    """Classify a filename into a single category."""
    source_path = source if source is not None else Path(name)
    kw = CATEGORY_KEYWORDS if keywords is None else keywords
    candidates = _collect_candidate_matches(name, keywords=kw)
    resolved = _resolve_single_category(candidates, priority=CATEGORY_PRIORITY)

    return ClassifiedFile(
        source=source_path,
        category=resolved.category,
        matched_keyword=resolved.matched_keyword or None,
    )


def classify_path(
    path: Path,
    *,
    keywords: dict[Category, tuple[str, ...]] | None = None,
) -> ClassifiedFile:
    """Classify a file path based on its name."""
    return classify_name(name=path.name, source=path, keywords=keywords)


def _get_candidate_matches(name: str) -> tuple[_CategoryMatch, ...]:
    """Return all category candidates for future interactive resolution."""
    return tuple(_collect_candidate_matches(name, keywords=CATEGORY_KEYWORDS))
