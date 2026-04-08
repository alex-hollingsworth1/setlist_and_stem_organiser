"""Interactive review helpers for planned actions."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .models import Category, PlannedAction


def review_actions(
    actions: list[PlannedAction],
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> list[PlannedAction]:
    """Review OTHER-category actions and return confirmed actions to execute."""
    auto_confirmed: list[PlannedAction] = []
    needs_review: list[PlannedAction] = []

    for action in actions:
        if action.category is Category.OTHER:
            needs_review.append(action)
        else:
            auto_confirmed.append(action)

    output_fn(f"Auto-classified {len(auto_confirmed)} files.")
    if not needs_review:
        return auto_confirmed

    output_fn(f"Reviewing {len(needs_review)} files in OTHER.")
    reviewed: list[PlannedAction] = []

    for action in needs_review:
        reviewed_action = _review_one_action(
            action=action,
            input_fn=input_fn,
            output_fn=output_fn,
        )
        if reviewed_action is not None:
            reviewed.append(reviewed_action)

    return auto_confirmed + reviewed


def _review_one_action(
    *,
    action: PlannedAction,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> PlannedAction | None:
    output_fn(f"File: {action.source.name}")
    while True:
        response = input_fn(
            "Enter=keep OTHER, category name=reassign, s=skip: "
        ).strip()
        if response == "":
            return action
        if response.lower() == "s":
            return None

        category = _parse_category(response)
        if category is None:
            output_fn("Invalid category. Try again.")
            continue

        destination = _destination_for_category(action.destination, category)
        return PlannedAction(
            source=action.source,
            destination=destination,
            category=category,
        )


def _parse_category(value: str) -> Category | None:
    candidate = value.strip().upper()
    try:
        return Category(candidate)
    except ValueError:
        return None


def _destination_for_category(destination: Path, category: Category) -> Path:
    return destination.parent.parent / category.value / destination.name
