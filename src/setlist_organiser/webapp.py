from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

from setlist_organiser.models import Category, PlannedAction
from setlist_organiser.organiser import execute_plan, output_folder_for_reveal
from setlist_organiser.planner import plan_organisation

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-insecure")


@app.get("/")
def index():
    return render_template(
        "index.html",
        actions=None,
        error=None,
        report=None,
        reveal_path=None,
        source_dir="../../AUDIO_FILES_FOR_TESTING",  # TEMP: hardcoded local test paths for development only
        output_root="output",  # TEMP: hardcoded local test paths for development only
        categories=Category,
    )


@app.post("/preview")
def preview():
    source_dir = request.form.get("source_dir", "").strip()
    output_root = request.form.get("output_root", "").strip()

    try:
        actions = plan_organisation(Path(source_dir), Path(output_root))
        return render_template(
            "index.html",
            actions=actions,
            error=None,
            report=None,
            reveal_path=None,
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
        source_dir="",
        output_root="",
        categories=Category,
    )


if __name__ == "__main__":
    app.run(debug=True)