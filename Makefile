test:
	source .venv/bin/activate && pytest -v

quiet:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --quiet

show-other:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --show-other

summary:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --summary-only

dry-run:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output --dry-run

run:
	source .venv/bin/activate && setlist-organiser ../../AUDIO_FILES_FOR_TESTING output



