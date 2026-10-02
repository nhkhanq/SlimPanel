VENV := .venv/bin

.PHONY: install test run import-preview import-apply clean

install:
	python3 -m venv .venv
	$(VENV)/python -m pip install --upgrade pip
	$(VENV)/python -m pip install -r requirements-dev.txt

test:
	$(VENV)/python -m pytest

run:
	$(VENV)/python runserver.py

import-preview:
	$(VENV)/python -m app.cli import-aapanel

import-apply:
	$(VENV)/python -m app.cli import-aapanel --apply

clean:
	rm -rf .pytest_cache **/__pycache__
