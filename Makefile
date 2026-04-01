PYTHON ?= python3

.PHONY: help install-dev test lint build clean check dist-check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install-dev: ## Install in editable mode with dev dependencies
	$(PYTHON) -m pip install -e ".[dev]"

test: ## Run the test suite
	$(PYTHON) -m pytest -q

test-verbose: ## Run the test suite with verbose output
	$(PYTHON) -m pytest -v

lint: ## Syntax-check all source files
	$(PYTHON) -m compileall src/ -q
	$(PYTHON) -m compileall tests/ -q

build: clean ## Build wheel and sdist
	$(PYTHON) -m build

clean: ## Remove build artifacts
	rm -rf dist/ build/ src/*.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

dist-check: build ## Build and verify distributions with twine
	$(PYTHON) -m twine check dist/* 2>/dev/null || pipx run twine check dist/*

check: lint test build ## Run lint, test, and build (full CI locally)
	@echo "All checks passed."
