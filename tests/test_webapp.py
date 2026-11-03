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
    assert "setlist-organiser" in html
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
    assert "Open in Finder" in html


def test_build_and_open_session_stores_path_in_session(client, tmp_path: Path):
    """Test that build_and_open_session stores the session path under the correct key."""
    import wave
    from setlist_organiser.webapp import SESSION_KEY_ABLETON_PATH
    
    source = tmp_path / "in"
    source.mkdir()
    
    kick_wav = source / "kick.wav"
    with wave.open(str(kick_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(b"\x00\x00" * 4410)
    
    with client.session_transaction() as sess:
        sess[SESSION_KEY_ABLETON_PATH] = None
    
    response = client.post(
        "/build-and-open-session",
        data={
            "source": [str(kick_wav)],
            "destination": [str(tmp_path / "out" / "DRUMS" / "kick.wav")],
            "category": ["DRUMS"],
        },
        follow_redirects=False,
    )
    
    assert response.status_code == 302
    
    with client.session_transaction() as sess:
        stored_path = sess.get(SESSION_KEY_ABLETON_PATH)
        assert stored_path is not None
        assert stored_path.endswith("session.als")
    
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Ableton session generated" in html
    
    response = client.get("/open-ableton-session", follow_redirects=False)
    assert response.status_code == 302
    
    with client.session_transaction() as sess:
        assert sess.get(SESSION_KEY_ABLETON_PATH) is None