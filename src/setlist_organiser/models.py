"""Shared domain models for the setlist organiser core."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Category(StrEnum):
    """Supported output categories for classified stems."""

    PERC = "PERC"
    DRUMS = "DRUMS"
    BASS = "BASS"
    SUB = "SUB"
    KEYS = "KEYS"
    GTR = "GTR"
    VOX = "VOX"
    BVS = "BVS"
    FX = "FX"
    CLICK = "CLICK"
    CUES = "CUES"
    STRINGS = "STRINGS"
    BRASS = "BRASS"
    WOODWIND = "WOODWIND"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class ClassifiedFile:
    """Classification result for a single input file."""

    source: Path
    category: Category
    matched_keyword: str | None = None


@dataclass(frozen=True, slots=True)
class PlannedAction:
    """A single copy operation derived from classification output."""

    source: Path
    destination: Path
    category: Category


@dataclass(frozen=True, slots=True)
class RunReport:
    """Structured run summary for dry-runs and real executions."""

    total_files: int
    copied_files: int
    dry_run: bool
