# Setlist Organiser

[![PyPI](https://img.shields.io/pypi/v/setlist-organiser)](https://pypi.org/project/setlist-organiser/)
[![Python](https://img.shields.io/pypi/pyversions/setlist-organiser)](https://pypi.org/project/setlist-organiser/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

CLI tool for classifying audio stem filenames into categories and organising them into folder structure via copy or move operations.

## What it does

- Scans a source folder for audio files
- Classifies each file by filename keywords (e.g. `DRUMS`, `BASS`, `VOX`)
- Copies or moves files to `OUTPUT_ROOT/<CATEGORY>/...`
- Supports dry-run, recursive scan, custom keyword config, and interactive review for `OTHER` files

## Requirements

- Python `>=3.11`

## Install

Install from PyPI:

```bash
pip install setlist-organiser
```

Or install from source:

```bash
git clone https://github.com/alex-hollingsworth1/setlist_and_stem_organiser.git
cd setlist_and_stem_organiser
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

This exposes the command:

```bash
setlist-organiser --help
```