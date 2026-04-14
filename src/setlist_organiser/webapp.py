from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template, request

from setlist_organiser.planner import plan_organisation

app = Flask(__name__)


@app.get("/")
def index():
    return render_template(
        "index.html",
        actions=None,
        error=None,
        source_dir="",
        output_root="",
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
            source_dir=source_dir,
            output_root=output_root,
        )
    except NotADirectoryError as exc:
        return render_template(
            "index.html",
            actions=None,
            error=str(exc),
            source_dir=source_dir,
            output_root=output_root,
        )


if __name__ == "__main__":
    app.run(debug=True)