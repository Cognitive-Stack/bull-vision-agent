.PHONY: install run test lint format clean

# Variables
PYTHON = poetry run python
PYTEST = poetry run pytest
BLACK = poetry run black
ISORT = poetry run isort
FLAKE8 = poetry run flake8
MYPY = poetry run mypy

# Default values for HOST and PORT
HOST ?= localhost
PORT ?= 8000

# Install dependencies
install:
	rm poetry.lock && poetry install --no-cache --no-interaction --no-root

# Run the application
run:
	poetry run uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

# Run tests
test:
	$(PYTEST) tests/ -v

# Lint the code
lint:
	$(FLAKE8) app/ bot/ tests/
	$(MYPY) app/ bot/ tests/

# Format the code
format:
	$(BLACK) app/ bot/ tests/
	$(ISORT) app/ bot/ tests/

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Development setup
setup: install format lint

# Run all checks
check: lint test

# Help
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run       - Run the application"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linters"
	@echo "  make format    - Format the code"
	@echo "  make clean     - Clean up generated files"
	@echo "  make setup     - Setup development environment"
	@echo "  make check     - Run all checks"
	@echo "  make help      - Show this help message" 