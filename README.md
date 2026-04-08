# Setlist Organiser

CLI tool for classifying audio stem filenames into categories and copying them into an organised folder structure.

## What it does

- Scans a source folder for audio files
- Classifies each file by filename keywords (e.g. `DRUMS`, `BASS`, `VOX`)
- Copies files to `OUTPUT_ROOT/<CATEGORY>/...`
- Supports dry-run, recursive scan, custom keyword config, and interactive review for `OTHER` files

## Requirements

- Python `>=3.11`

## Install

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

This exposes the command:

```bash
setlist-organiser --help
```

## Basic usage

```bash
setlist-organiser SOURCE_DIR OUTPUT_ROOT
```

Example:

```bash
setlist-organiser ../../AUDIO_FILES_FOR_TESTING output
```

For paths with spaces, quote them:

```bash
setlist-organiser "/path/with spaces/Stems '24" output
```

## Common flags

- `--dry-run`  
  Show what would be copied without writing files.
- `--quiet`  
  Suppress per-file listing.
- `--summary-only`  
  Print category counts.
- `--show-other`  
  Print files currently classified as `OTHER`.
- `--recursive`  
  Scan nested folders.
- `--config PATH`  
  Load extra keyword mappings from a JSON config file.
- `--review`  
  Interactively review files in `OTHER` before execution.

## Interactive review mode

Use review mode to handle uncertain files before copying:

```bash
setlist-organiser SOURCE_DIR OUTPUT_ROOT --review
```

For each `OTHER` file:

- Press `Enter` to keep as `OTHER`
- Type a category name (e.g. `DRUMS`, `VOX`, `KEYS`) to reassign
- Type `s` to skip the file

## Config file format

Config adds extra keywords per category (it does not remove built-in defaults).

Example `test_config.json`:

```json
{
  "keywords": {
    "DRUMS": ["room", "hh"],
    "VOX": ["adlib_fx"]
  }
}
```

Run with config:

```bash
setlist-organiser SOURCE_DIR OUTPUT_ROOT --config test_config.json
```

## Output behavior

- `--dry-run`: no files are copied
- normal run: files are copied using metadata-preserving copy
- destination collisions are suffixed (`_2`, `_3`, ...)

## Development

Run tests:

```bash
pytest -v
```

Or use Makefile shortcuts:

```bash
make test
make dry-run
make review
make summary
```
