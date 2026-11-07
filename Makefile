# Setlist & Stem Organiser — agent-friendly Make targets
# Prefer these over assuming a pre-existing .venv (see AGENTS.md).

SOURCE_DIR ?= ../../AUDIO_FILES_FOR_TESTING
OUTPUT_DIR ?= output
SESSION ?= $(OUTPUT_DIR)/session.als

# Use .venv when present; otherwise the current Python interpreter.
PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else command -v python3 || command -v python; fi)
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
CLI := $(PYTHON) -m setlist_organiser.cli

.DEFAULT_GOAL := help

.PHONY: help install install-dev test \
	test-webapp test-cli test-planner test-organiser test-config \
	test-classifier test-reviewer test-session \
	web web-5001 \
	quiet show-other review summary dry-run move-dry run build-session \
	doctor

help:
	@echo "Setlist & Stem Organiser"
	@echo "  PYTHON      = $(PYTHON)"
	@echo ""
	@echo "Setup"
	@echo "  make install       Editable install (runtime deps)"
	@echo "  make install-dev   Editable install + pytest"
	@echo "  make doctor        Print interpreter / package sanity"
	@echo ""
	@echo "Tests"
	@echo "  make test          Full pytest suite"
	@echo "  make test-<module> webapp|cli|planner|organiser|config|classifier|reviewer|session"
	@echo ""
	@echo "App"
	@echo "  make web           Flask UI on default port (local only)"
	@echo "  make web-5001      Flask UI on :5001"
	@echo "  make dry-run / run / quiet / show-other / review / summary / move-dry"
	@echo "                     Organise stems (SOURCE_DIR / OUTPUT_DIR overridable)"
	@echo "  make build-session Organise + write Ableton session (SESSION overridable)"

doctor:
	@echo "PYTHON=$(PYTHON)"
	@$(PYTHON) -c "import sys; print('version', sys.version)"
	@$(PYTHON) -c "import setlist_organiser, flask, lxml; print('imports ok')" 2>/dev/null \
		|| echo "package not importable — run: make install-dev"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

test:
	$(PYTEST) -v

test-webapp:
	$(PYTEST) -v tests/test_webapp.py

test-cli:
	$(PYTEST) -v tests/test_cli.py

test-planner:
	$(PYTEST) -v tests/test_planner.py

test-organiser:
	$(PYTEST) -v tests/test_organiser.py

test-config:
	$(PYTEST) -v tests/test_config.py

test-classifier:
	$(PYTEST) -v tests/test_classifier.py

test-reviewer:
	$(PYTEST) -v tests/test_reviewer.py

test-session:
	$(PYTEST) -v tests/test_session_builder.py

web:
	$(PYTHON) -m setlist_organiser.webapp

web-5001:
	FLASK_APP=setlist_organiser.webapp $(PYTHON) -m flask run --port 5001

quiet:
	$(CLI) $(SOURCE_DIR) $(OUTPUT_DIR) --quiet

show-other:
	$(CLI) $(SOURCE_DIR) $(OUTPUT_DIR) --show-other

review:
	$(CLI) $(SOURCE_DIR) $(OUTPUT_DIR) --review

summary:
	$(CLI) $(SOURCE_DIR) $(OUTPUT_DIR) --summary-only

dry-run:
	$(CLI) $(SOURCE_DIR) $(OUTPUT_DIR) --dry-run

move-dry:
	$(CLI) $(SOURCE_DIR) $(OUTPUT_DIR) --move --dry-run

run:
	$(CLI) $(SOURCE_DIR) $(OUTPUT_DIR)

build-session:
	$(CLI) $(SOURCE_DIR) $(OUTPUT_DIR) --build-session $(SESSION)
