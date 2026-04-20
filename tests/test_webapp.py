from pathlib import Path

from setlist_organiser.webapp import app

import pytest

@pytest.fixture
def client():
    app.config["TESTING"] = True 
    with app.test_client() as client:
        yield client

def test_index_route_renders_form(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert "Stem Organiser Preview" in html
    assert "source_dir" in html
    assert "output_root" in html

def test_preview_route_shows_planned_actions(client, tmp_path: Path):
    source = tmp_path / "in"
    source.mkdir()
    (source / "kick.wav").write_bytes(b"")

    output = tmp_path / "out"

    response = client.post(
        "/preview",
        data={
            "source_dir": str(source),
            "output_root": str(output),
        },
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Planned actions" in html
    assert "kick.wav" in html
    assert "DRUMS" in html

def test_preview_route_invalid_source_shows_error(client, tmp_path: Path):
    output = tmp_path / "out"

    response = client.post(
        "/preview",
        data={
            "source_dir": str(tmp_path / "does_not_exist"),
            "output_root": str(output),
        },
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Source is not a directory" in html


def test_execute_route_copies_files_and_shows_report(client, tmp_path: Path):
    source = tmp_path / "in"
    source.mkdir()
    source_file = source / "kick.wav"
    source_file.write_bytes(b"123")
    destination = tmp_path / "out" / "DRUMS" / "kick.wav"

    response = client.post(
        "/execute",
        data={
            "source": [str(source_file)],
            "destination": [str(destination)],
            "category": ["DRUMS"],
        },
    )

    assert response.status_code == 200
    assert destination.exists()
    html = response.get_data(as_text=True)
    assert "Successfully copied 1 files." in html