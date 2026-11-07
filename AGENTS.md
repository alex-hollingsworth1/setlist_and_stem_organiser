# AGENTS.md — Setlist & Stem Organiser

This repo is a **small, deterministic playground** for agent orchestration:
classify audio stems by filename, copy/move them into category folders, and
optionally build an Ableton Live `.als` session from a packaged template.

Use this file as the contract for Cloud Agents, Cursor Automations, and local
multi-agent experiments. Prefer it over guessing from chat history.

## Why this repo works for orchestration practice

- Pure-Python core with fast `pytest` (no network on the happy path).
- Clear pipeline boundaries that map cleanly to agent tickets.
- Ableton XML work is awkward for humans but well-scoped for agents.
- Surfaces (CLI / Flask / Python API) already drift — good material for
  parity, eval, and “one PR per lever” drills.

## Quick start (agents)

```bash
python3 -m pip install -e ".[dev]"
make test
# or: python3 -m pytest -v
```

Do **not** assume `.venv` exists. Prefer `make …` (falls back to the current
Python) or `python3 -m pytest` / `python3 -m setlist_organiser…`.

| Goal | Command |
| --- | --- |
| Full test suite | `make test` |
| One module | `make test-classifier` / `test-cli` / `test-webapp` / … |
| Local web UI | `make web` (loopback only — see Security) |
| Dry-run organise | `make dry-run SOURCE_DIR=… OUTPUT_DIR=…` |
| Install editable + dev deps | `make install` |

Python `>=3.11`. Runtime deps: `flask`, `lxml`. Dev: `pytest`.

## Architecture (keep tickets inside one stage when possible)

```
SOURCE_DIR audio files
        │
        ▼
  classifier.py   filename → Category (+ matched keyword)
        │
        ▼
  planner.py      → list[PlannedAction]  (dest under OUTPUT_ROOT/<CATEGORY>/)
        │
        ├─ reviewer.py     interactive OTHER reassignment (CLI)
        ├─ organiser.py    copy2 / move (+ optional macOS Finder reveal)
        └─ session_builder.py + resources/AH_BLANK - 2.als
                           → session.als (group + colour-coded tracks)
```

| Path | Role |
| --- | --- |
| `src/setlist_organiser/models.py` | `Category`, `ClassifiedFile`, `PlannedAction`, `RunReport` |
| `src/setlist_organiser/classifier.py` | Keyword tables + priority resolver |
| `src/setlist_organiser/planner.py` | Scan audio, allocate destinations |
| `src/setlist_organiser/organiser.py` | Execute plan |
| `src/setlist_organiser/reviewer.py` | CLI OTHER review |
| `src/setlist_organiser/config.py` | JSON keyword overrides |
| `src/setlist_organiser/session_builder.py` | Ableton XML clone / wire / warp |
| `src/setlist_organiser/templates.py` | Packaged template path (+ env override) |
| `src/setlist_organiser/cli.py` | Console entrypoint `setlist-organiser` |
| `src/setlist_organiser/webapp.py` | Flask local UI |
| `tests/` | Module tests — extend these when changing behaviour |

Template override: `SETLIST_ORGANISER_ABLETON_TEMPLATE=/path/to/file.als`.

## Hard rules for agents

1. **One lever per PR.** Do not mix classifier keyword changes with Ableton
   XML refactors or web UI redesigns in the same change.
2. **Never expand `CATEGORY_KEYWORDS` without updating / adding golden
   fixtures.** Short tokens (`hit`, `lv`, `oh`, `sc`, `rim`, `double`, …)
   already false-positive on song titles. Prefer tests that lock intended
   behaviour over “more keywords.”
3. **CLI and web are one product.** If you add a flag/behaviour to one
   surface, either mirror it on the other or document the intentional gap
   in the PR. Current known drift: web preview lacks recursive / numbered /
   move / dry-run; Ableton session build is web + Python API only (not CLI).
4. **`session_builder.py` ↔ packaged `.als` are coupled.** Change both, and
   keep/extend XML structure tests in `tests/test_session_builder.py`.
5. **Do not expose the Flask app.** It accepts arbitrary filesystem paths and
   uses a insecure default `SECRET_KEY` for local use. Treat as desktop-only.
6. **macOS-only:** Finder reveal and `open` for Ableton no-op elsewhere —
   fine; do not invent cross-platform GUI open unless asked.
7. **Keep deps light by default.** Heavy audio ML (Essentia, Librosa, etc.)
   belongs behind optional extras and only after a keyword eval baseline
   exists. Open issues #2 / #3 are not free-for-alls.
8. **Prefer `make` / `python3 -m`.** Do not require a pre-existing `.venv`.

## Good agent ticket shapes (orchestration drills)

Size work so a single agent can finish and prove it with `make test`.

| Ticket shape | Example acceptance |
| --- | --- |
| Classifier golden set | Fixture of stem names → expected `Category`; suite fails on regressions for `hit_the_road` / `double_espresso` style cases |
| CLI `--build-session` | Headless organise + write `.als` without Flask; test covers exit code + file exists |
| Reviewer + `--numbered` | Reassign OTHER under `05_DRUMS/`-style paths without breaking dest layout |
| Surface parity | Web gains dry-run or recursive to match CLI; tests for both |
| Lint gate | `ruff` (and optionally `mypy`) in CI + `make lint` |
| Optional extras | `[web]` / `[ableton]` extras; core install stays minimal |
| Eval harness | Metrics for OTHER rate / false-positive rate on a named fixture corpus |

Label GitHub issues **`agent-ready`** only when the description has: goal,
out-of-scope, acceptance commands, and files likely touched.

## Orchestration recipes to practice here

Use this repo to rehearse patterns, not to overbuild the product.

1. **Issue → Cloud Agent → PR** — open a tightly scoped `agent-ready` issue;
   agent implements; human reviews diff + `make test`.
2. **Eval loop** — pin a stem-name fixture; agent changes one classifier
   lever; remeasure; keep or revert.
3. **Parity audit** — agent diffs CLI flags vs web routes vs README; opens
   a PR that closes one gap only.
4. **Bugbot / CI on every PR** — keep Tests workflow green; add lint when
   ready so agent PRs get mechanical feedback.
5. **Stacked small PRs** — classifier fixtures, then CLI session flag, then
   web parity — rather than one mega-PR.

Avoid starting with issue #2 (Essentia) until keyword fixtures exist; native
audio stacks burn orchestration time without a regression baseline.

## Security & local tool assumptions

- Flask is a **local desktop helper**, not a deployed service.
- Default `SECRET_KEY` is insecure by design for local runs; do not deploy.
- `/execute` and `/build-and-open-session` read/write paths from the form —
  never bind to a public interface.
- Generated `.als` may be uncompressed XML; Ableton Live opens that and
  recompresses on save.

## Done when

- `make test` (or `python3 -m pytest -v`) is green.
- Behaviour changes have tests; keyword changes have fixture coverage.
- PR description states which pipeline stage moved and what was left alone.
- No secrets committed; no assumption that `.venv` was pre-created.
