from pathlib import Path

from lxml import etree

from setlist_organiser.models import Category, PlannedAction
from setlist_organiser.session_builder import build_session, parse_template


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "AH_BLANK Project" / "AH_BLANK - 2.als"


def _localname(element: etree._Element) -> str:
    return etree.QName(element).localname


def test_build_session_groups_audio_tracks_under_group_tracks(tmp_path: Path) -> None:
    actions = [
        PlannedAction(
            source=Path("/in/kick.wav"),
            destination=tmp_path / "DRUMS" / "kick.wav",
            category=Category.DRUMS,
        ),
        PlannedAction(
            source=Path("/in/snare.wav"),
            destination=tmp_path / "DRUMS" / "snare.wav",
            category=Category.DRUMS,
        ),
        PlannedAction(
            source=Path("/in/bass1.wav"),
            destination=tmp_path / "BASS" / "bass1.wav",
            category=Category.BASS,
        ),
        PlannedAction(
            source=Path("/in/bass2.wav"),
            destination=tmp_path / "BASS" / "bass2.wav",
            category=Category.BASS,
        ),
    ]

    template = parse_template(TEMPLATE_PATH)
    output_path = tmp_path / "session.als"
    build_session(template, actions, output_path)

    tree = etree.parse(str(output_path))
    tracks = next(el for el in tree.iter() if _localname(el) == "Tracks")
    children = list(tracks)

    group_tracks = [c for c in children if _localname(c) == "GroupTrack"]
    audio_tracks = [c for c in children if _localname(c) == "AudioTrack"]

    assert len(group_tracks) == 2
    assert len(audio_tracks) == 4

    def effective_name(track: etree._Element) -> str:
        node = next(
            el for el in track.iter() if _localname(el) == "EffectiveName"
        )
        return node.get("Value")

    assert {effective_name(gt) for gt in group_tracks} == {"DRUMS", "BASS"}
    assert {effective_name(at) for at in audio_tracks} == {
        "kick",
        "snare",
        "bass1",
        "bass2",
    }

    group_ids = {int(gt.get("Id")) for gt in group_tracks}
    for at in audio_tracks:
        track_group_id_node = next(
            el for el in at.iter() if _localname(el) == "TrackGroupId"
        )
        assert int(track_group_id_node.get("Value")) in group_ids

    expected_pairs = {
        ("DRUMS", "kick"),
        ("DRUMS", "snare"),
        ("BASS", "bass1"),
        ("BASS", "bass2"),
    }
    group_id_to_name = {int(gt.get("Id")): effective_name(gt) for gt in group_tracks}
    actual_pairs = set()
    for at in audio_tracks:
        track_group_id_node = next(
            el for el in at.iter() if _localname(el) == "TrackGroupId"
        )
        parent_name = group_id_to_name[int(track_group_id_node.get("Value"))]
        actual_pairs.add((parent_name, effective_name(at)))
    assert actual_pairs == expected_pairs


def test_build_session_assigns_unique_track_ids_and_updates_next_pointee(
    tmp_path: Path,
) -> None:
    actions = [
        PlannedAction(
            source=Path("/in/kick.wav"),
            destination=tmp_path / "DRUMS" / "kick.wav",
            category=Category.DRUMS,
        ),
        PlannedAction(
            source=Path("/in/bass1.wav"),
            destination=tmp_path / "BASS" / "bass1.wav",
            category=Category.BASS,
        ),
    ]

    template = parse_template(TEMPLATE_PATH)
    output_path = tmp_path / "session.als"
    build_session(template, actions, output_path)

    tree = etree.parse(str(output_path))
    tracks = next(el for el in tree.iter() if _localname(el) == "Tracks")
    new_track_ids = [
        int(c.get("Id"))
        for c in tracks
        if _localname(c) in {"GroupTrack", "AudioTrack"}
    ]
    assert len(new_track_ids) == len(set(new_track_ids))

    all_ids = []
    for element in tree.iter():
        id_value = element.get("Id")
        if id_value is None:
            continue
        try:
            all_ids.append(int(id_value))
        except ValueError:
            continue

    next_pointee = next(el for el in tree.iter() if _localname(el) == "NextPointeeId")
    assert int(next_pointee.get("Value")) == max(all_ids) + 1


def test_build_session_keeps_children_adjacent_to_their_group(tmp_path: Path) -> None:
    actions = [
        PlannedAction(
            source=Path("/in/kick.wav"),
            destination=tmp_path / "DRUMS" / "kick.wav",
            category=Category.DRUMS,
        ),
        PlannedAction(
            source=Path("/in/snare.wav"),
            destination=tmp_path / "DRUMS" / "snare.wav",
            category=Category.DRUMS,
        ),
        PlannedAction(
            source=Path("/in/bass1.wav"),
            destination=tmp_path / "BASS" / "bass1.wav",
            category=Category.BASS,
        ),
    ]

    template = parse_template(TEMPLATE_PATH)
    output_path = tmp_path / "session.als"
    build_session(template, actions, output_path)

    tree = etree.parse(str(output_path))
    tracks = next(el for el in tree.iter() if _localname(el) == "Tracks")
    children = [c for c in tracks if _localname(c) in {"GroupTrack", "AudioTrack"}]

    current_group_id: int | None = None
    for child in children:
        if _localname(child) == "GroupTrack":
            current_group_id = int(child.get("Id"))
        else:
            track_group_id_node = next(
                el for el in child.iter() if _localname(el) == "TrackGroupId"
            )
            assert int(track_group_id_node.get("Value")) == current_group_id
