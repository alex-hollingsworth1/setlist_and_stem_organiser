import json
from pathlib import Path

from .models import Category


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
