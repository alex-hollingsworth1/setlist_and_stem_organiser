from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

from setlist_organiser.classifier import CATEGORY_KEYWORDS
from setlist_organiser.models import Category, PlannedAction
from setlist_organiser.organiser import execute_plan, output_folder_for_reveal
from setlist_organiser.planner import plan_organisation
from setlist_organiser.session_builder import build_session, parse_template
from setlist_organiser.config import (
    build_effective_keywords,
    load_keyword_overrides,
    merge_keywords_into_stored_overrides,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-insecure")


def keyword_overrides_path() -> Path:
    """
    Canonical JSON file for web-app keyword overrides (extra tokens only).

    :func:`merge_keywords_into_stored_overrides` appends to this file;
    :func:`load_keyword_overrides` + :func:`build_effective_keywords` merge it
    with :data:`CATEGORY_KEYWORDS` when planning, same as the CLI ``--config`` flow.
    """
    return Path(app.instance_path) / "keyword_overrides.json"


@app.get("/")
def index():
    ableton_message = session.pop("ableton_build_message", None)
    ableton_path = session.get("reveal-ableton-session")
    return render_template(
        "index.html",
        actions=None,
        error=None,
        report=None,
        reveal_path=None,
        ableton_message=ableton_message,
        ableton_path=ableton_path,
        source_dir="",
        output_root="",
        categories=Category,
    )


def _planning_keywords() -> dict[Category, tuple[str, ...]] | None:
    """
    If ``instance/keyword_overrides.json`` exists and is valid, return
    ``build_effective_keywords(CATEGORY_KEYWORDS, loaded_overrides)``; else ``None`` for built-ins only.
    """
    path = keyword_overrides_path()
    if not path.is_file():
        return None
    overrides = load_keyword_overrides(path)
    return build_effective_keywords(CATEGORY_KEYWORDS, overrides)


@app.post("/preview")
def preview():
    source_dir = request.form.get("source_dir", "").strip()
    output_root = request.form.get("output_root", "").strip()

    try:
        try:
            keywords = _planning_keywords()
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            return render_template(
                "index.html",
                actions=None,
                error=f"Invalid keyword overrides file: {exc}",
                report=None,
                reveal_path=None,
                ableton_message=None,
                ableton_path=None,
                source_dir=source_dir,
                output_root=output_root,
                categories=Category,
            )
        actions = plan_organisation(
            Path(source_dir), Path(output_root), keywords=keywords
        )
        return render_template(
            "index.html",
            actions=actions,
            error=None,
            report=None,
            reveal_path=None,
            ableton_message=None,
            ableton_path=None,
            source_dir=source_dir,
            output_root=output_root,
            categories=Category,
        )
    except NotADirectoryError as exc:
        return render_template(
            "index.html",
            actions=None,
            error=str(exc),
            report=None,
            reveal_path=None,
            ableton_message=None,
            ableton_path=None,
            source_dir=source_dir,
            output_root=output_root,
            categories=Category,
        )


@app.get("/reveal-in-finder")
def reveal_in_finder():
    path_str = session.pop("reveal_output_path", None)
    if not path_str:
        return redirect(url_for("index"))
    folder = Path(path_str)
    if not folder.is_dir():
        return redirect(url_for("index"))
    if sys.platform == "darwin":
        subprocess.run(
            ["open", str(folder)],
            check=False,
            capture_output=True,
        )
    return redirect(url_for("index"))


@app.get("/open-ableton-session")
def open_in_ableton():
    path_str = session.pop("reveal-ableton-session", None)
    if not path_str:
        return redirect(url_for("index"))
    als_file = Path(path_str)
    if not als_file.is_file():
        return redirect(url_for("index"))
    if sys.platform == "darwin":
        subprocess.run(
            ["open", str(als_file)],
            check=False,
            capture_output=True,
        )
    return redirect(url_for("index"))


@app.post("/execute")
def execute():
    sources = request.form.getlist("source")
    destinations = request.form.getlist("destination")
    categories = request.form.getlist("category")

    actions: list[PlannedAction] = []
    for source, destination, category in zip(sources, destinations, categories):
        actions.append(
            PlannedAction(
                source=Path(source),
                destination=Path(destination),
                category=Category(category),
            )
        )

    report = execute_plan(actions, dry_run=False, reveal_in_finder=False)

    reveal_path = None
    folder = output_folder_for_reveal(actions)
    if folder is not None and report.copied_files > 0 and not report.dry_run:
        session["reveal_output_path"] = str(folder)
        reveal_path = str(folder)

    return render_template(
        "index.html",
        report=report,
        actions=None,
        error=None,
        reveal_path=reveal_path,
        ableton_message=None,
        ableton_path=None,
        source_dir="",
        output_root="",
        categories=Category,
    )


@app.post("/build-and-open-session")
def build_and_open_session():
    sources = request.form.getlist("source")
    destinations = request.form.getlist("destination")
    categories = request.form.getlist("category")

    actions: list[PlannedAction] = []
    for source, destination, category in zip(sources, destinations, categories):
        actions.append(
            PlannedAction(
                source=Path(source),
                destination=Path(destination),
                category=Category(category),
            )
        )

    if not actions:
        session["ableton_build_message"] = (
            "No planned actions available to build a session."
        )
        return redirect(url_for("index"))

    source_root = Path(os.path.commonpath([str(a.source) for a in actions]))
    if source_root.is_file():
        source_root = source_root.parent
    output_path = source_root / "ABLETON" / "session.als"

    project_root = Path(__file__).resolve().parent.parent.parent
    template_path = project_root / "AH_BLANK Project" / "AH_BLANK.als"
    if not template_path.is_file():
        session["ableton_build_message"] = f"Template not found: {template_path}"
        return redirect(url_for("index"))

    parsed_template = parse_template(template_path)
    build_session(parsed_template, actions, output_path)

    if sys.platform == "darwin":
        subprocess.run(["open", str(output_path)], check=False, capture_output=True)

    session["open-ableton-session"] = str(output_path)
    session["ableton_build_message"] = f"Ableton session generated: {output_path}"
    return redirect(url_for("index"))


@app.post("/add-keywords")
def add_keywords():
    category_name = request.form.get("category_name", "").strip().upper()
    new_keywords = request.form.get("new_keywords", "").strip()
    split_keywords = tuple(new_keywords.split())

    if not split_keywords:
        return redirect(url_for("index"))
    if category_name not in Category.__members__:
        raise ValueError("Must be a valid category.")
    merge_keywords_into_stored_overrides(
        keyword_overrides_path(), Category[category_name], split_keywords
    )
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Disable the Werkzeug reloader when SETLIST_NO_RELOAD=1 so debugpy hits this process
    # (otherwise a child process serves requests and breakpoints may not bind).
    use_reloader = os.environ.get("SETLIST_NO_RELOAD") not in ("1", "true", "yes")
    app.run(debug=True, use_reloader=use_reloader)
