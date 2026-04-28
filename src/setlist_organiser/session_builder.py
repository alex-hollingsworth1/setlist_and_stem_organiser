"""Parse Ableton Live (.als) templates for building sessions from organised stems."""

from __future__ import annotations

from copy import deepcopy
import gzip
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
    Category.BASS: 9,
    Category.SUB: 4,
    Category.KEYS: 1,
    Category.GTR: 5,
    Category.VOX: 7,
    Category.BVS: 8,
    Category.FX: 3,
    Category.CLICK: 10,
    Category.CUES: 11,
    Category.STRINGS: 12,
    Category.BRASS: 15,
    Category.WOODWIND: 14,
    Category.OTHER: 15,
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


def _clone_track(
    template_track: etree._Element, category: Category, track_id: int, start_id: int
) -> tuple[etree._Element, int]:
    """
    Deep copy a template AudioTrack and apply ID, name, colour, and sub-IDs.
    """
    cloned = deepcopy(template_track)
    cloned.set("Id", str(track_id))

    name_value = category.value
    name_set = _set_first_value_attr(cloned, "UserName", name_value)
    effective_set = _set_first_value_attr(cloned, "EffectiveName", name_value)
    if not name_set or not effective_set:
        raise ValueError(
            "Template AudioTrack is missing UserName/EffectiveName Value nodes."
        )

    colour_node = _first_descendant_by_localname(cloned, "Color")
    if colour_node is None:
        raise ValueError("Template AudioTrack is missing a Color node.")
    colour_node.set("Value", str(CATEGORY_COLOURS[category]))
    next_available_id = _iter_sub_id_values(cloned, start_id=start_id)
    return cloned, next_available_id


def build_session(
    template: ParsedAbletonTemplate, actions: list[PlannedAction], output_path: Path
) -> None:
    """
    Build a new session XML by replacing template tracks with category tracks.
    """
    categories = {action.category for action in actions}
    ordered_categories = [c for c in CATEGORY_PRIORITY if c in categories]
    remaining = sorted(categories - set(ordered_categories), key=lambda c: c.value)
    ordered_categories.extend(remaining)

    tracks_container = _first_descendant_by_localname(template.root, "Tracks")
    if tracks_container is None:
        raise ValueError("Template XML does not contain a <Tracks> element.")

    for child in list(tracks_container):
        if etree.QName(child).localname == "AudioTrack":
            tracks_container.remove(child)

    current_max_id = max(_iter_id_values(template.root), default=0)
    for category in ordered_categories:
        track_id = current_max_id + 1
        cloned_track, next_available_id = _clone_track(
            template.template_track,
            category,
            track_id=track_id,
            start_id=track_id,
        )
        tracks_container.append(cloned_track)
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
