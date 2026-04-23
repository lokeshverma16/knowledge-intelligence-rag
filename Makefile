.PHONY: install dev test lint run up down clean

PYTHON ?= python3

install:  ## Install runtime deps into the current env
	$(PYTHON) -m pip install -r requirements.txt

dev:  ## Install dev + test deps
	$(PYTHON) -m pip install -r requirements-dev.txt

test:  ## Run the offline test suite
	ENVIRONMENT=testing $(PYTHON) -m pytest

run:  ## Run the Flask dev server locally (embedded Chroma)
	$(PYTHON) run.py

up:  ## Boot the full stack (api + chromadb) via docker-compose
	docker compose up --build

down:  ## Tear it back down
	docker compose down

clean:
	rm -rf data/chromadb data/chromadb-test __pycache__ .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
