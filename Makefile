test:
	source .venv/bin/activate && pytest -v

quiet:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --quiet

show-other:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --show-other

review:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --review

summary:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --summary-only

dry-run:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --dry-run

move-dry:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --move --dry-run

run:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output
