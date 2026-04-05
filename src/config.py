import json
from pathlib import Path
from .models import Category

def load_keyword_overrides(path: Path):
    text = path.read_text()
    data = json.loads(text)

    # Validate the JSON data and make sure the categories exist
    for category_name in data["keywords"]:
        if category_name not in Category.__members__:
            raise ValueError(f"Unknown category: {category_name}")

    # Build return value
    result = {}
    for category_name, keywords in data["keywords"].items():
        result[Category(category_name)] = tuple(keywords)

    return result


def build_effective_keywords(defaults: dict[Category, tuple[str]], overrides: dict[Category, tuple[str]]) -> dict[Category, tuple[str]]:
    merged = {}
    for category, keywords in defaults.items():
        if category in overrides:
            merged[category] = keywords + overrides[category]
        else:
            merged[category] = keywords

    return merged