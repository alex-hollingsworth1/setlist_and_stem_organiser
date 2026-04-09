from pathlib import Path
from setlist_organiser.models import PlannedAction, Category
from setlist_organiser.organiser import execute_plan

def test_dry_run_does_not_copy(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    out = tmp_path / "out"
    (source / "song_keys_piano.wav").write_bytes(b"")

    actions = [
        PlannedAction(
            source=source / "song_keys_piano.wav",
            destination=out / "KEYS" / "song_keys_piano.wav",
            category=Category.KEYS,
        )
    ]

    report = execute_plan(actions=actions, dry_run=True)
    assert not (out / "KEYS" / "song_keys_piano.wav").exists()


def test_real_run_copy_files(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    out = tmp_path / "out"
    (source / "song_keys_piano.wav").write_bytes(b"")

    actions = [
        PlannedAction(
            source=source / "song_keys_piano.wav",
            destination=out / "KEYS" / "song_keys_piano.wav",
            category=Category.KEYS,
        )
    ]

    report = execute_plan(actions=actions, dry_run=False)
    assert (out / "KEYS" / "song_keys_piano.wav").exists()
    assert (source / "song_keys_piano.wav").exists() 

def test_dry_run_does_not_move(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    out = tmp_path / "out"
    (source / "song_keys_piano.wav").write_bytes(b"")

    actions = [
        PlannedAction(
            source=source / "song_keys_piano.wav",
            destination=out / "KEYS" / "song_keys_piano.wav",
            category=Category.KEYS,
        )
    ]

    report = execute_plan(actions=actions, dry_run=True, move=True)
    assert not (out / "KEYS" / "song_keys_piano.wav").exists()

def test_real_run_move_files(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    out = tmp_path / "out"
    (source / "song_keys_piano.wav").write_bytes(b"")

    actions = [
        PlannedAction(
            source=source / "song_keys_piano.wav",
            destination=out / "KEYS" / "song_keys_piano.wav",
            category=Category.KEYS,
        )
    ]

    report = execute_plan(actions=actions, dry_run=False, move=True)
    assert (out / "KEYS" / "song_keys_piano.wav").exists()
    assert not (source / "song_keys_piano.wav").exists()  



