SOURCE_DIR ?= ../../AUDIO_FILES_FOR_TESTING
OUTPUT_DIR ?= output

test:
	source .venv/bin/activate && pytest -v

test-webapp:
	source .venv/bin/activate && pytest -v tests/test_webapp.py

test-cli:
	source .venv/bin/activate && pytest -v tests/test_cli.py

test-planner:
	source .venv/bin/activate && pytest -v tests/test_planner.py

test-organiser:
	source .venv/bin/activate && pytest -v tests/test_organiser.py

test-config:
	source .venv/bin/activate && pytest -v tests/test_config.py

web:
	source .venv/bin/activate && python -m setlist_organiser.webapp

web-5001:
	source .venv/bin/activate && FLASK_APP=setlist_organiser.webapp flask run --port 5001

quiet:
	source .venv/bin/activate && setlist-organiser $(SOURCE_DIR) $(OUTPUT_DIR) --quiet

show-other:
	source .venv/bin/activate && setlist-organiser $(SOURCE_DIR) $(OUTPUT_DIR) --show-other

review:
	source .venv/bin/activate && setlist-organiser $(SOURCE_DIR) $(OUTPUT_DIR) --review

summary:
	source .venv/bin/activate && setlist-organiser $(SOURCE_DIR) $(OUTPUT_DIR) --summary-only

dry-run:
	source .venv/bin/activate && setlist-organiser $(SOURCE_DIR) $(OUTPUT_DIR) --dry-run

move-dry:
	source .venv/bin/activate && setlist-organiser $(SOURCE_DIR) $(OUTPUT_DIR) --move --dry-run

run:
	source .venv/bin/activate && setlist-organiser $(SOURCE_DIR) $(OUTPUT_DIR)
