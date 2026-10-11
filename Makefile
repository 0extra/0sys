.PHONY: help install install-dev test test-unit test-integration lint format typecheck clean build docs

help:
	@echo "Available targets:"
	@echo "  install           Install package"
	@echo "  install-dev       Install package with dev dependencies"
	@echo "  test              Run all tests"
	@echo "  test-unit         Run unit tests"
	@echo "  test-integration  Run integration tests"
	@echo "  lint              Run ruff"
	@echo "  format            Run ruff format"
	@echo "  typecheck         Run mypy"
	@echo "  clean             Clean build artifacts"
	@echo "  build             Build wheel and sdist"
	@echo "  docs              Build documentation"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

test-unit:
	pytest tests/unit -m unit

test-integration:
	pytest tests/integration -m integration

lint:
	ruff check src tests

format:
	ruff format src tests
	ruff check --fix src tests

typecheck:
	mypy src/zerosys

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

build:
	python -m build

docs:
	mkdocs build