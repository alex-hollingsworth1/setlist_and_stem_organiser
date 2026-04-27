"""Parse Ableton Live (.als) templates for building sessions from organised stems."""

from __future__ import annotations

import gzip
import io
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


@dataclass(slots=True)
class ParsedAbletonTemplate:
    """
    Result of reading an Ableton project or template.
    """

    tree: etree._ElementTree
    root: etree._Element
    template_track: etree._Element


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
