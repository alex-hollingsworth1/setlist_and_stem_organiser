"""Parse Ableton Live (.als) templates for building sessions from organised stems."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import gzip
import wave
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lxml import etree
from .classifier import CATEGORY_PRIORITY
from .models import Category, PlannedAction


@dataclass(slots=True)
class ParsedAbletonTemplate:
    """
    Result of reading an Ableton project or template.
    """

    tree: etree._ElementTree
    root: etree._Element
    template_track: etree._Element


CATEGORY_COLOURS: dict[Category, int] = {
    Category.PERC: 14,
    Category.DRUMS: 14,
    Category.BASS: 64,
    Category.SUB: 64,
    Category.KEYS: 1,
    Category.GTR: 5,
    Category.VOX: 26,
    Category.BVS: 26,
    Category.FX: 3,
    Category.CLICK: 55,
    Category.CUES: 55,
    Category.STRINGS: 58,
    Category.BRASS: 58,
    Category.WOODWIND: 58,
    Category.OTHER: 42,
}


def _is_gzip(data: bytes) -> bool:
    return len(data) >= 2 and data[:2] == b"\x1f\x8b"


def _decompress_ableton_file(path: Path) -> bytes:
    """Return raw project XML bytes, whether the file is gzip-wrapped or plain XML."""
    data = path.read_bytes()
    if _is_gzip(data):
        return gzip.decompress(data)
    return data


def _first_audio_track(root: etree._Element, path: Path) -> etree._Element:
    for el in root.iter():
        if etree.QName(el).localname == "AudioTrack":
            return el
    raise ValueError(
        f"Expected at least one <AudioTrack> in the project XML, none found: {path}"
    )


def _first_group_track(root: etree._Element) -> etree._Element:
    for el in root.iter():
        if etree.QName(el).localname == "GroupTrack":
            return el
    raise ValueError("Template XML does not contain a <GroupTrack> element.")


def _first_audio_clip(track: etree._Element) -> etree._Element:
    for el in track.iter():
        if etree.QName(el).localname == "AudioClip":
            return el
    raise ValueError("AudioTrack XML does not contain an <AudioClip> element.")


def parse_template(path: Path) -> ParsedAbletonTemplate:
    """
    Read an Ableton Live session file and extract the first audio track as a template.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Not a file: {path}")

    xml_bytes = _decompress_ableton_file(path)
    tree = etree.parse(io.BytesIO(xml_bytes))
    root = tree.getroot()
    template_track = _first_audio_track(root, path)
    return ParsedAbletonTemplate(
        tree=tree,
        root=root,
        template_track=template_track,
    )


def _first_descendant_by_localname(
    element: etree._Element, local_name: str
) -> etree._Element | None:
    for child in element.iter():
        if etree.QName(child).localname == local_name:
            return child
    return None


def _set_first_value_attr(parent: etree._Element, local_name: str, value: str) -> bool:
    node = _first_descendant_by_localname(parent, local_name)
    if node is None:
        return False
    node.set("Value", value)
    return True


def _iter_id_values(root: etree._Element) -> Iterable[int]:
    for element in root.iter():
        id_value = element.get("Id")
        if id_value is None:
            continue
        try:
            yield int(id_value)
        except ValueError:
            continue


def _iter_sub_id_values(track: etree._Element, start_id: int) -> int:
    """
    Reassign descendant ``Id`` attributes to unique values.
    """
    next_id = start_id + 1
    for element in track.iterdescendants():
        if element.get("Id") is None:
            continue
        element.set("Id", str(next_id))
        next_id += 1
    return next_id


def _clear_take_lanes_content(track: etree._Element) -> None:
    """
    Empty ``<TakeLanes><TakeLanes>`` (remove all ``<TakeLane>`` children) and fold lanes.

    Leaves the main clip slot untouched; only nested take-lane clip data is removed.
    """
    outer_take_lanes = None
    for child in track:
        if etree.QName(child).localname == "TakeLanes":
            outer_take_lanes = child
            break
    if outer_take_lanes is None:
        raise ValueError("AudioTrack is missing a <TakeLanes> element.")

    inner_take_lanes = None
    for child in outer_take_lanes:
        if etree.QName(child).localname == "TakeLanes":
            inner_take_lanes = child
            break
    if inner_take_lanes is None:
        raise ValueError("AudioTrack <TakeLanes> is missing inner <TakeLanes>.")

    for lane in list(inner_take_lanes):
        inner_take_lanes.remove(lane)

    if not _set_first_value_attr(outer_take_lanes, "AreTakeLanesFolded", "true"):
        raise ValueError("AudioTrack <TakeLanes> is missing AreTakeLanesFolded.")


def _clone_track(
    template_track: etree._Element,
    category: Category,
    track_id: int,
    start_id: int,
    track_group_id: int,
    name: str,
    file_path: Path | None = None,
) -> tuple[etree._Element, int]:
    """
    Deep copy a template AudioTrack and apply ID, name, colour, group, and sub-IDs.
    """
    cloned = deepcopy(template_track)
    cloned.set("Id", str(track_id))

    name_set = _set_first_value_attr(cloned, "UserName", name)
    effective_set = _set_first_value_attr(cloned, "EffectiveName", name)
    if not name_set or not effective_set:
        raise ValueError(
            "Template AudioTrack is missing UserName/EffectiveName Value nodes."
        )

    if not _set_first_value_attr(cloned, "MemorizedFirstClipName", name):
        raise ValueError(
            "Template AudioTrack is missing MemorizedFirstClipName Value node."
        )

    if not _set_first_value_attr(cloned, "TrackGroupId", str(track_group_id)):
        raise ValueError("Template AudioTrack is missing a TrackGroupId Value node.")

    colour_node = _first_descendant_by_localname(cloned, "Color")
    if colour_node is None:
        raise ValueError("Template AudioTrack is missing a Color node.")
    colour_node.set("Value", str(CATEGORY_COLOURS[category]))
    next_available_id = _iter_sub_id_values(cloned, start_id=start_id)

    if file_path is not None:
        template_clips = [
            el
            for el in template_track.iter()
            if etree.QName(el).localname == "AudioClip"
        ]
        cloned_clips = [
            el for el in cloned.iter() if etree.QName(el).localname == "AudioClip"
        ]
        if not template_clips:
            raise ValueError("Template AudioTrack does not contain any <AudioClip>.")
        if len(template_clips) != len(cloned_clips):
            raise ValueError(
                "Cloned track AudioClip count does not match template ("
                f"{len(cloned_clips)} vs {len(template_clips)})."
            )
        parent_map = {child: parent for parent in cloned.iter() for child in parent}
        clip_next_id = next_available_id
        for template_clip, existing_clip in zip(
            template_clips, cloned_clips, strict=True
        ):
            cloned_clip, clip_next_id = _clone_audio_clip(
                template_clip=template_clip,
                file_path=file_path,
                clip_name=name,
                colour=CATEGORY_COLOURS[category],
                start_id=clip_next_id - 1,
                template_root=template_track.getroottree().getroot(),
            )
            clip_parent = parent_map.get(existing_clip)
            if clip_parent is None:
                raise ValueError("Template AudioTrack AudioClip has no parent node.")
            clip_parent.replace(existing_clip, cloned_clip)
        next_available_id = clip_next_id

    _clear_take_lanes_content(cloned)

    return cloned, next_available_id


def _clone_folder_track(
    template_group_track: etree._Element,
    category: Category,
    track_id: int,
    start_id: int,
) -> tuple[etree._Element, int]:
    """
    Deep copy a template GroupTrack and apply ID, name, colour, and sub-IDs.
    """
    cloned = deepcopy(template_group_track)
    cloned.set("Id", str(track_id))

    name_value = category.value
    name_set = _set_first_value_attr(cloned, "UserName", name_value)
    effective_set = _set_first_value_attr(cloned, "EffectiveName", name_value)
    if not name_set or not effective_set:
        raise ValueError(
            "Template GroupTrack is missing UserName/EffectiveName Value nodes."
        )

    colour_node = _first_descendant_by_localname(cloned, "Color")
    if colour_node is None:
        raise ValueError("Template GroupTrack is missing a Color node.")
    colour_node.set("Value", str(CATEGORY_COLOURS[category]))
    next_available_id = _iter_sub_id_values(cloned, start_id=start_id)
    return cloned, next_available_id


def _clone_audio_clip(
    template_clip: etree._Element,
    file_path: Path,
    clip_name: str,
    colour: int,
    start_id: int,
    template_root: etree._Element,
) -> tuple[etree._Element, int]:
    """
    Deep copy a template AudioClip and apply file path, clip name, and sub-IDs.
    """
    cloned = deepcopy(template_clip)
    _set_first_value_attr(cloned, "SampleVolume", "1")

    try:
        with wave.open(str(file_path), "rb") as wf:
            frame_count = wf.getnframes()
            sample_rate = wf.getframerate()
    except wave.Error:
        frame_count = None
        sample_rate = None

    file_size = file_path.stat().st_size

    clip_seconds: float | None = None
    clip_beats: float | None = None
    if frame_count is not None and sample_rate is not None:
        main_track = _first_descendant_by_localname(template_root, "MainTrack")
        tempo = 120.0
        if main_track is not None:
            tempo_el = _first_descendant_by_localname(main_track, "Tempo")
            if tempo_el is not None:
                manual_el = _first_descendant_by_localname(tempo_el, "Manual")
                if manual_el is not None and manual_el.get("Value") is not None:
                    try:
                        tempo = float(manual_el.get("Value", "120"))
                    except ValueError:
                        tempo = 120.0
        clip_seconds = frame_count / float(sample_rate)
        clip_beats = clip_seconds * (tempo / 60.0)
        beats_str = str(clip_beats)
    else:
        beats_str = None

    file_path_value = file_path.as_posix()
    file_refs: list[etree._Element] = []
    for sample_ref in cloned.iter():
        if etree.QName(sample_ref).localname != "SampleRef":
            continue
        for child in sample_ref:
            local = etree.QName(child).localname
            if local == "FileRef":
                file_refs.append(child)
            elif local == "DefaultDuration":
                child.set(
                    "Value",
                    str(frame_count) if frame_count is not None else "0",
                )
            elif local == "DefaultSampleRate":
                child.set(
                    "Value",
                    str(sample_rate) if sample_rate is not None else "0",
                )

    if not file_refs:
        raise ValueError(
            "Template AudioClip is missing a FileRef as a direct child of SampleRef."
        )

    path_updated = False
    for file_ref_node in file_refs:
        path_node = _first_descendant_by_localname(file_ref_node, "Path")
        if path_node is not None:
            path_node.set("Value", file_path_value)
            path_updated = True

        relative_path_node = _first_descendant_by_localname(
            file_ref_node, "RelativePath"
        )
        if relative_path_node is not None:
            relative_path_node.set("Value", file_path_value)

        file_name_node = _first_descendant_by_localname(file_ref_node, "Name")
        if file_name_node is not None:
            file_name_node.set("Value", file_path.name)

        original_size = _first_descendant_by_localname(
            file_ref_node, "OriginalFileSize"
        )
        if original_size is not None:
            original_size.set("Value", str(file_size))
        original_crc = _first_descendant_by_localname(file_ref_node, "OriginalCrc")
        if original_crc is not None:
            original_crc.set("Value", "0")

    if not path_updated:
        raise ValueError("Template AudioClip FileRef is missing a Path Value node.")

    name_node = next(
        (
            child
            for child in cloned
            if etree.QName(child).localname == "Name" and child.get("Value") is not None
        ),
        None,
    )
    if name_node is None:
        raise ValueError("Template AudioClip is missing a Name Value node.")
    name_node.set("Value", clip_name)
    _set_first_value_attr(cloned, "Color", str(colour))

    if beats_str is not None:
        current_end = _first_descendant_by_localname(cloned, "CurrentEnd")
        if current_end is not None:
            current_end.set("Value", beats_str)
        loop_el = _first_descendant_by_localname(cloned, "Loop")
        if loop_el is not None:
            for tag in ("LoopEnd", "OutMarker", "HiddenLoopEnd"):
                node = _first_descendant_by_localname(loop_el, tag)
                if node is not None:
                    node.set("Value", beats_str)

        warp_markers = _first_descendant_by_localname(cloned, "WarpMarkers")
        if warp_markers is not None:
            for child in list(warp_markers):
                warp_markers.remove(child)
            etree.SubElement(
                warp_markers,
                "WarpMarker",
                attrib={
                    "Id": "0",
                    "SecTime": "0",
                    "BeatTime": "0",
                },
            )
            etree.SubElement(
                warp_markers,
                "WarpMarker",
                attrib={
                    "Id": "1",
                    "SecTime": str(clip_seconds),
                    "BeatTime": str(clip_beats),
                },
            )

    next_available_id = _iter_sub_id_values(cloned, start_id=start_id)
    return cloned, next_available_id


def build_session(
    template: ParsedAbletonTemplate, actions: list[PlannedAction], output_path: Path
) -> None:
    """
    Build a new session XML by replacing template tracks with category tracks.
    """
    actions_by_category: dict[Category, list[PlannedAction]] = defaultdict(list)
    for action in actions:
        actions_by_category[action.category].append(action)

    categories = set(actions_by_category)
    ordered_categories = [c for c in CATEGORY_PRIORITY if c in categories]
    remaining = sorted(categories - set(ordered_categories), key=lambda c: c.value)
    ordered_categories.extend(remaining)

    tracks_container = _first_descendant_by_localname(template.root, "Tracks")
    if tracks_container is None:
        raise ValueError("Template XML does not contain a <Tracks> element.")

    template_group_track = _first_group_track(template.root)
    current_max_id = max(_iter_id_values(template.root), default=0)

    for child in list(tracks_container):
        if etree.QName(child).localname in {"AudioTrack", "GroupTrack"}:
            tracks_container.remove(child)

    for category in ordered_categories:
        group_track_id = current_max_id + 1
        cloned_group, next_available_id = _clone_folder_track(
            template_group_track,
            category,
            track_id=group_track_id,
            start_id=group_track_id,
        )
        tracks_container.append(cloned_group)
        current_max_id = next_available_id - 1

        for action in actions_by_category[category]:
            audio_track_id = current_max_id + 1
            cloned_audio, next_available_id = _clone_track(
                template.template_track,
                category,
                track_id=audio_track_id,
                start_id=audio_track_id,
                track_group_id=group_track_id,
                name=action.destination.stem,
                file_path=action.source,
            )
            tracks_container.append(cloned_audio)
            current_max_id = next_available_id - 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    next_pointee = _first_descendant_by_localname(template.root, "NextPointeeId")
    if next_pointee is not None:
        next_pointee.set("Value", str(current_max_id + 1))

    template.tree.write(
        str(output_path),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )
