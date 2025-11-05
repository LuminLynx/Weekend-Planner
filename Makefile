# Makefile for Weekend Plan Synthesizer

.PHONY: help install test run clean docker-build docker-run dev lint image

help:
	@echo "Available commands:"
	@echo "  make install                      - install dependencies"
	@echo "  make test                         - run unit tests"
	@echo "  make run DATE=YYYY-MM-DD BUDGET=30- run the planner demo"
	@echo "  make dev                          - run dev server with reload"
	@echo "  make lint                         - run code linters"
	@echo "  make image                        - build docker image"
	@echo "  make clean                        - remove caches"
	@echo "  make docker-build                 - build docker image (alias for image)"
	@echo "  make docker-run DATE=YYYY-MM-DD BUDGET=30 - run inside docker"

install:
	pip install -e .

test:
	pytest -q

run:
	python app/main.py --date $(DATE) --budget-pp $(BUDGET) --with-dining

dev:
	uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

lint:
	@echo "Running linters..."
	@if command -v ruff >/dev/null 2>&1; then \
		echo "Running ruff..."; \
		ruff check app/ || true; \
	fi
	@if command -v black >/dev/null 2>&1; then \
		echo "Running black..."; \
		black --check app/ || true; \
	fi
	@if command -v mypy >/dev/null 2>&1; then \
		echo "Running mypy..."; \
		mypy app/ || true; \
	else \
		echo "Linters not installed. Install with: pip install ruff black mypy"; \
		python -m py_compile app/**/*.py || true; \
	fi

image:
	docker build -t weekend-planner:latest .

docker-build: image

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .cache
	rm -f fx_last_good.json
	rm -rf data/

docker-run:
	docker run --rm -p 8000:8000 weekend-planner:latest --date $(DATE) --budget-pp $(BUDGET) --with-dining
