.PHONY: help install test lint format clean run ingest

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean generated files"
	@echo "  make run         - Run the chat application"
	@echo "  make ingest      - Run document ingestion"
	@echo "  make dev-setup   - Complete development setup"

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pip install pytest pytest-cov pytest-asyncio black pylint mypy isort

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov=config --cov-report=html --cov-report=term

lint:
	pylint app/ config/ scripts/
	mypy app/ config/ scripts/

format:
	black app/ config/ scripts/ tests/
	isort app/ config/ scripts/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/

run:
	python main.py

ingest:
	python scripts/ingest.py

dev-setup: install-dev
	@echo "Installing Ollama models..."
	ollama pull nomic-embed-text
	ollama pull llama3.1:8b-instruct-q4_K_M
	@echo "✅ Development environment ready!"

check: lint test
	@echo "✅ All checks passed!"
