import json
from pathlib import Path

from .models import Category


def _dedupe_keywords_preserve_order(keywords: tuple[str, ...]) -> tuple[str, ...]:
    """Drop duplicates (case-insensitive), keep the first occurrence’s spelling."""
    seen: set[str] = set()
    out: list[str] = []
    for w in keywords:
        key = w.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(w)
    return tuple(out)


def load_keyword_overrides(path: Path) -> dict[Category, tuple[str, ...]]:
    text = path.read_text()
    data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("Config must be a JSON object at the top level")
    
    if "keywords" not in data:
        raise ValueError("Config must contain a 'keywords' field")
    
    if not isinstance(data["keywords"], dict):
        raise ValueError("'keywords' must be an object mapping categories to keyword lists")

    for category_name in data["keywords"]:
        if category_name not in Category.__members__:
            raise ValueError(f"Unknown category: {category_name}")

    result: dict[Category, tuple[str, ...]] = {}
    for category_name, keywords in data["keywords"].items():
        result[Category(category_name)] = tuple(keywords)

    return result

def save_keyword_overrides(path: Path, overrides: dict[Category, tuple[str, ...]]) -> None:
    kw_dict: dict[str, list[str]] = {}
    for category, words in overrides.items():
        kw_dict[str(category)] = list(words)
    data = {"keywords": kw_dict}
    path.write_text(json.dumps(data, indent=2))


def merge_keywords_into_stored_overrides(
    path: Path,
    category: Category,
    new_tokens: tuple[str, ...],
) -> None:
    """
    Update the JSON overrides file: for ``category``, append new tokens to any
    already stored for that category, de-duplicated (case-insensitive). Other
    categories in the file are left unchanged. Matches how
    :func:`build_effective_keywords` uses the file: file holds only the extra
    keywords; defaults + overrides are merged at planning time.
    """
    if not new_tokens:
        return
    if path.is_file():
        existing = load_keyword_overrides(path)
    else:
        existing = {}
    prior = existing.get(category, ())
    combined = _dedupe_keywords_preserve_order(prior + new_tokens)
    existing[category] = combined
    path.parent.mkdir(parents=True, exist_ok=True)
    save_keyword_overrides(path, existing)


def build_effective_keywords(
    defaults: dict[Category, tuple[str, ...]],
    overrides: dict[Category, tuple[str, ...]],
) -> dict[Category, tuple[str, ...]]:
    merged: dict[Category, tuple[str, ...]] = {}
    for category, keywords in defaults.items():
        if category in overrides:
            merged[category] = keywords + overrides[category]
        else:
            merged[category] = keywords

    return merged
