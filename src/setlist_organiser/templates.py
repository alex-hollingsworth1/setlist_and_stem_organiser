"""Helper functions for accessing package resource files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import ContextManager

try:
    from importlib.resources import as_file, files
except ImportError:
    from importlib_resources import as_file, files  # type: ignore


def get_ableton_template_path() -> ContextManager[Path]:
    """
    Return the path to the default Ableton template file.
    
    The path is managed via a context manager that ensures proper cleanup
    of any temporary extractions when the package is zipped.
    
    Can be overridden via the SETLIST_ORGANISER_ABLETON_TEMPLATE environment variable.
    
    Example:
        with get_ableton_template_path() as template_path:
            parsed = parse_template(template_path)
    """
    env_override = os.environ.get("SETLIST_ORGANISER_ABLETON_TEMPLATE")
    if env_override:
        # For environment override, return a simple context manager
        from contextlib import nullcontext
        return nullcontext(Path(env_override))
    
    template_file = files("setlist_organiser.resources").joinpath("AH_BLANK - 2.als")
    return as_file(template_file)
