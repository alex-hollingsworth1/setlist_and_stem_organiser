from pathlib import Path

from setlist_organiser.models import Category, PlannedAction
from setlist_organiser.reviewer import review_actions


def test_review_actions_enter_keeps_other() -> None:
    actions = [
        PlannedAction(
            source=Path("/tmp/song_stem.wav"),
            destination=Path("/out/OTHER/song_stem.wav"),
            category=Category.OTHER,
        )
    ]
    responses = iter([""])

    result = review_actions(actions, input_fn=lambda _prompt: next(responses))

    assert len(result) == 1
    assert result[0].category == Category.OTHER
    assert result[0].destination == Path("/out/OTHER/song_stem.wav")


def test_review_actions_reassigns_category_and_destination() -> None:
    actions = [
        PlannedAction(
            source=Path("/tmp/song_stem.wav"),
            destination=Path("/out/OTHER/song_stem.wav"),
            category=Category.OTHER,
        )
    ]
    responses = iter(["DRUMS"])

    result = review_actions(actions, input_fn=lambda _prompt: next(responses))

    assert len(result) == 1
    assert result[0].category == Category.DRUMS
    assert result[0].destination == Path("/out/DRUMS/song_stem.wav")


def test_review_actions_skip_excludes_action() -> None:
    actions = [
        PlannedAction(
            source=Path("/tmp/song_stem.wav"),
            destination=Path("/out/OTHER/song_stem.wav"),
            category=Category.OTHER,
        )
    ]
    responses = iter(["s"])

    result = review_actions(actions, input_fn=lambda _prompt: next(responses))

    assert result == []


def test_review_actions_invalid_then_retry() -> None:
    actions = [
        PlannedAction(
            source=Path("/tmp/song_stem.wav"),
            destination=Path("/out/OTHER/song_stem.wav"),
            category=Category.OTHER,
        )
    ]
    responses = iter(["not_a_category", "keys"])
    output: list[str] = []

    result = review_actions(
        actions,
        input_fn=lambda _prompt: next(responses),
        output_fn=output.append,
    )

    assert len(result) == 1
    assert result[0].category == Category.KEYS
    assert result[0].destination == Path("/out/KEYS/song_stem.wav")
    assert "Invalid category. Try again." in output
