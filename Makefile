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

# Add these targets to your existing Makefile

.PHONY: docker-build docker-up docker-down docker-logs docker-clean docker-restart docker-shell docker-dev

# Production Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker containers (production)..."
	docker-compose up -d
	@echo "✅ Services started. Use 'make docker-logs' to view logs"

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-logs-app:
	docker-compose logs -f rag-agent

docker-logs-ollama:
	docker-compose logs -f ollama

docker-restart:
	@echo "Restarting services..."
	docker-compose restart

docker-clean:
	@echo "Removing containers, networks, and volumes..."
	docker-compose down -v
	docker system prune -f

docker-shell:
	@echo "Opening shell in rag-agent container..."
	docker-compose exec rag-agent /bin/bash

docker-shell-ollama:
	@echo "Opening shell in ollama container..."
	docker-compose exec ollama /bin/bash

docker-ingest:
	@echo "Running document ingestion in container..."
	docker-compose exec rag-agent python scripts/ingest.py

docker-stats:
	docker stats rag-agent-app rag-ollama

docker-pull-models:
	@echo "Pulling Ollama models..."
	docker-compose exec ollama ollama pull nomic-embed-text
	docker-compose exec ollama ollama pull llama3.1:8b-instruct-q4_K_M

# Development Docker commands
docker-dev:
	@echo "Starting Docker containers (development with hot reload)..."
	docker-compose -f docker-compose.dev.yml up

docker-dev-build:
	@echo "Building development Docker images..."
	docker-compose -f docker-compose.dev.yml build

docker-dev-up:
	@echo "Starting development containers in background..."
	docker-compose -f docker-compose.dev.yml up -d

docker-dev-down:
	@echo "Stopping development containers..."
	docker-compose -f docker-compose.dev.yml down

docker-dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

docker-dev-restart:
	@echo "Restarting development services..."
	docker-compose -f docker-compose.dev.yml restart

docker-dev-shell:
	@echo "Opening shell in development container..."
	docker-compose -f docker-compose.dev.yml exec rag-agent-dev /bin/bash

docker-dev-clean:
	@echo "Cleaning development environment..."
	docker-compose -f docker-compose.dev.yml down -v

# Complete Docker setup
docker-setup: docker-build docker-up
	@echo "Waiting for services to be ready..."
	@sleep 15
	@echo "Pulling models..."
	@make docker-pull-models
	@echo "✅ Docker setup complete!"

docker-dev-setup: docker-dev-build docker-dev-up
	@echo "Waiting for services to be ready..."
	@sleep 15
	@echo "Pulling models..."
	@docker-compose -f docker-compose.dev.yml exec ollama ollama pull nomic-embed-text
	@docker-compose -f docker-compose.dev.yml exec ollama ollama pull llama3.1:8b-instruct-q4_K_M
	@echo "✅ Development Docker setup complete!"

# Quick start with Docker
docker-quick:
	@echo "Quick starting with Docker Compose..."
	docker-compose up -d