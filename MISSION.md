# Mission: Setlist Organiser — Architecture & Data Flow

## Why
Alex maintains and extends this codebase (CLI + web UI for classifying/organising audio stems, with optional Ableton session creation) and wants to work on it faster and more independently — adding features, fixing bugs, and reviewing changes without having to re-derive how the modules fit together each session.

## Success looks like
- Can trace a request from an entry point (CLI `main()` or Flask `webapp.py`) all the way through to output (copied/moved files, or a generated `.als` session) without opening every file to check.
- Can name which module (`classifier`, `planner`, `organiser`, `reviewer`, `session_builder`, `config`) a given feature request or bug report belongs to before searching.
- Can explain the core data pipeline (`ClassifiedFile` → `PlannedAction` → `RunReport`) and where the web UI and Ableton session builder attach to it.
- Can explain how the Ableton `.als` XML template is manipulated by `session_builder.py` (tracks, clips, warp markers) well enough to extend it.

## Constraints
- Short bursts, as time allows — no scheduled long sessions. Lessons should be small, self-contained wins.

## Out of scope
- General Ableton Live *usage* (as a DAW end-user) — this is about the codebase that manipulates `.als` files, not performing in Live.
- PyPI packaging/release mechanics and CI config, unless a bug is actually traced there.
- Flask internals beyond what `webapp.py` actually uses.
