"""Golden stem-name corpus: product intent for classify_name.

Stretch-tagged rows and rows with enforce=false are documented only.
Do not expand CATEGORY_KEYWORDS without updating tests/fixtures/stems.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from setlist_organiser.classifier import classify_name
from setlist_organiser.models import Category

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "stems.json"


def _load_enforced_cases() -> list[tuple[str, Category]]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases: list[tuple[str, Category]] = []
    for row in payload["cases"]:
        tags = set(row.get("tags", []))
        if "stretch" in tags:
            continue
        if row.get("enforce", True) is False:
            continue
        cases.append((row["name"], Category(row["category"])))
    return cases


@pytest.mark.parametrize(
    ("name", "expected"),
    _load_enforced_cases(),
    ids=lambda value: value if isinstance(value, str) else value.value,
)
def test_golden_stem_classification(name: str, expected: Category) -> None:
    classified = classify_name(name)
    assert classified.category == expected, (
        f"{name!r}: expected {expected.value}, "
        f"got {classified.category.value} "
        f"(matched_keyword={classified.matched_keyword!r})"
    )
