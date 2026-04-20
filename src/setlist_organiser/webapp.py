from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template, request

from setlist_organiser.models import Category, PlannedAction
from setlist_organiser.organiser import execute_plan
from setlist_organiser.planner import plan_organisation

app = Flask(__name__)


@app.get("/")
def index():
    return render_template(
        "index.html",
        actions=None,
        error=None,
        report=None,
        source_dir="../../AUDIO_FILES_FOR_TESTING", # TEMP: hardcoded local test paths for development only
        output_root="output", # TEMP: hardcoded local test paths for development only
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
            source_dir=source_dir,
            output_root=output_root,
            categories=Category,
        )


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

    report = execute_plan(actions, dry_run=False)
    return render_template(
        "index.html",
        report=report,
        actions=None,
        error=None,
        source_dir="",
        output_root="",
        categories=Category,
    )


if __name__ == "__main__":
    app.run(debug=True)