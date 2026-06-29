# Setlist & Stem Organiser

[![PyPI](https://img.shields.io/pypi/v/setlist-organiser)](https://pypi.org/project/setlist-organiser/)
[![Python](https://img.shields.io/pypi/pyversions/setlist-organiser)](https://pypi.org/project/setlist-organiser/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

# Setlist & Stem Organiser

A Python tool for preparing live and session audio stems. It classifies stem files by name and sorts them into category folders — and, given an Ableton Live template, builds a ready-to-open `.als` session with every stem placed on its own track, grouped and colour-coded by category.

## Requirements

- Python `>=3.11`
- `lxml` (for session generation)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Organising stems

Scan a folder, classify each audio file by filename, and copy it into `OUTPUT_ROOT/<CATEGORY>/`:

```bash
setlist-organiser SOURCE_DIR OUTPUT_ROOT
```

Files are sorted into fixed categories (`DRUMS`, `BASS`, `VOX`, `KEYS`, `FX`, and so on), with `--dry-run`, `--move`, and `--recursive` available. Run `setlist-organiser --help` for the full set.

## Ableton session generation

Given an existing Live project as a template, the tool builds a complete session from a classified batch — each stem on its own audio track, grouped and colour-coded by category, ready to open in Live.

Ableton `.als` files are gzip-wrapped XML. The builder reads the template, reuses its first audio track and group track as blueprints, and for each stem:

- Rewrites the clip's sample reference to point at the real source file
- Reads the `.wav` header to set clip duration and fit it to the project tempo
- Regenerates warp markers so the clip sits correctly on the timeline
- Assigns unique element IDs so every new track and clip stays valid

Tracks are emitted in category order, so the session mirrors the folder layout.

Session generation runs from Python:

```python
from pathlib import Path
from setlist_organiser.planner import plan_organisation
from setlist_organiser.session_builder import parse_template, build_session

actions = plan_organisation(Path("stems/"), Path("output/"))
template = parse_template(Path("template.als"))
build_session(template, actions, Path("output/session.als"))
```

The template `.als` needs at least one audio track and one group track. Stems are best supplied as `.wav`, since duration and tempo-fitting read WAV headers.

## Development

```bash
pytest -v
```
