# Makefile for Weekend Plan Synthesizer

.PHONY: help install test run clean docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install                      - install dependencies"
	@echo "  make test                         - run unit tests"
	@echo "  make run DATE=YYYY-MM-DD BUDGET=30- run the planner demo"
	@echo "  make clean                        - remove caches"
	@echo "  make docker-build                 - build docker image"
	@echo "  make docker-run DATE=YYYY-MM-DD BUDGET=30 - run inside docker"

install:
	pip install -e .

test:
	pytest -q

run:
	python app/main.py --date $(DATE) --budget-pp $(BUDGET) --with-dining

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

docker-build:
	docker build -t weekend-planner:latest .

docker-run:
	docker run --rm -p 8000:8000 weekend-planner:latest --date $(DATE) --budget-pp $(BUDGET) --with-dining
