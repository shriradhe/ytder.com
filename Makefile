.PHONY: help install dev-install run test clean lint format type-check

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make run           - Run the application"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code with black"
	@echo "  make type-check    - Run type checker"
	@echo "  make clean         - Clean build artifacts"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black flake8 mypy

run:
	python start.py

test:
	pytest tests/ -v

lint:
	flake8 src/ main.py start.py --max-line-length=100 --exclude=__pycache__

format:
	black src/ main.py start.py --line-length=100

type-check:
	mypy src/ main.py --ignore-missing-imports

clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

