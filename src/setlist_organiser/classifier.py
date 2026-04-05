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
    ),
    Category.DRUMS: (
        "drum",
        "drums",
        "kit",
        "snare",
        "kick",
        "toms",
        "hihat",
        "hi hat",
        "ride",
        "crash",
        "overhead",
        "oh",
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
        "synth",
        "synths",
        "synth pad",
    ),
    Category.GTR: (
        "gtr",
        "guitar",
        "acoustic",
        "electric",
        "lead gtr",
        "rhythm gtr",
        "lead gtr",
        "rhythm gtr",
    ),
    Category.VOX: (
        "vox",
        "voc",
        "vocal",
        "lead vox",
        "lead vocal",
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
    ),
    Category.FX: (
        "fx",
        "sfx",
        "impact",
        "riser",
        "sweep",
        "transition",
    ),
    Category.CLICK: (
        "click",
        "metronome",
        "metro",
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
    Category.STRINGS,
    Category.BRASS,
    Category.WOODWIND,
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


def _collect_candidate_matches(name: str) -> list[_CategoryMatch]:
    normalized_name = _normalize_name(Path(name).stem)
    tokens = _tokenize(normalized_name)
    candidates: list[_CategoryMatch] = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if _keyword_matches(keyword, normalized_name, tokens):
                candidates.append(
                    _CategoryMatch(category=category, matched_keyword=keyword)
                )
                break

    return candidates


def _resolve_single_category(
    candidates: list[_CategoryMatch],
) -> _CategoryMatch:
    if not candidates:
        return _CategoryMatch(
            category=Category.OTHER,
            matched_keyword="",
        )

    candidate_by_category = {candidate.category: candidate for candidate in candidates}
    for category in CATEGORY_PRIORITY:
        if category in candidate_by_category:
            return candidate_by_category[category]

    return _CategoryMatch(category=Category.OTHER, matched_keyword="")


def classify_name(name: str, source: Path | None = None) -> ClassifiedFile:
    """Classify a filename into a single category."""
    source_path = source if source is not None else Path(name)
    candidates = _collect_candidate_matches(name)
    resolved = _resolve_single_category(candidates)

    return ClassifiedFile(
        source=source_path,
        category=resolved.category,
        matched_keyword=resolved.matched_keyword or None,
    )


def classify_path(path: Path) -> ClassifiedFile:
    """Classify a file path based on its name."""
    return classify_name(name=path.name, source=path)


def _get_candidate_matches(name: str) -> tuple[_CategoryMatch, ...]:
    """Return all category candidates for future interactive resolution."""
    return tuple(_collect_candidate_matches(name))
