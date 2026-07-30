# Setlist Organiser Architecture Resources

## Knowledge

- [README.md](./README.md)
  Top-level description of what the tool does and how it's installed. Use for: onboarding framing, confirming public-facing behaviour matches internals.
- [pyproject.toml](./pyproject.toml)
  Package metadata, dependencies (`flask`, `lxml`), entry point (`setlist-organiser = setlist_organiser.cli:main`). Use for: confirming what's a real dependency vs. incidental, finding the CLI entry point.
- `src/setlist_organiser/models.py`
  The three core dataclasses (`ClassifiedFile`, `PlannedAction`, `RunReport`) and the `Category` enum. Use for: the shared vocabulary every other module passes around.
- `src/setlist_organiser/classifier.py`, `planner.py`, `organiser.py`, `reviewer.py`, `cli.py`
  The core classify → plan → execute pipeline and its CLI wiring. Use for: lesson 1 (this is the spine of the app).
- `src/setlist_organiser/session_builder.py`, `webapp.py`
  Ableton `.als` XML generation and the Flask web UI. Use for: later lessons — these are the two things that sit "around" the core pipeline.
- `tests/*.py`
  Executable spec for each module — mirrors `src/setlist_organiser/*.py` one-to-one. Use for: verifying a claim about behaviour rather than trusting a docstring; a great place to check edge cases (e.g. `test_session_builder.py` for warp marker / tempo behaviour).
- Git history (`git log --oneline`)
  Recent commit messages describe why the session-builder features were added (e.g. TrackGroupId wiring, stem path wiring). Use for: understanding *why* a piece of code looks the way it does, not just what it does.

## Wisdom (Communities)

- No community sourcing needed yet — this is a solo/small codebase, not a topic with an external practitioner community. Skip unless a specific dependency (Flask, lxml, Ableton's Live XML format) needs outside troubleshooting.

## Gaps

- No internal architecture doc exists yet (no `CLAUDE.md`, no `ARCHITECTURE.md`). Lessons and reference docs produced here are the first written record — keep them accurate since there's nothing else to cross-check against except the source itself.
