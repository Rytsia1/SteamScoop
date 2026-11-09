.PHONY: help dev-setup validate-env up down down-v restart build logs ps lint format typecheck test test-backend test-frontend migrate check clean

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "SteamScoop Development Command Suite"
	@echo "====================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev-setup: ## Bootstrap local environment (.env template, Python venv, npm install)
	@echo "==> Initializing .env configuration..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; else echo ".env already exists"; fi
	@echo "==> Installing frontend dependencies..."
	npm --prefix apps/web install
	@echo "==> Setting up backend virtualenv..."
	python3 -m venv apps/api/.venv
	apps/api/.venv/bin/pip install --upgrade pip
	apps/api/.venv/bin/pip install -e "apps/api[dev]"
	@echo "==> Local development setup complete!"

validate-env: ## Run environment and dependency diagnostic checks
	@python3 scripts/validate_env.py

up: ## Start all Docker Compose containers in the background
	docker compose up -d

down: ## Stop all Docker Compose containers
	docker compose down

down-v: ## Stop containers and remove volumes (wipes database and cache)
	docker compose down -v

restart: ## Restart all containers
	docker compose restart

build: ## Build container images without caching issues
	docker compose build

logs: ## Follow Docker Compose container logs
	docker compose logs -f

ps: ## Check status and health of all containers
	docker compose ps

lint: ## Run linting for backend (Ruff) and frontend (ESLint)
	@echo "==> Linting backend..."
	apps/api/.venv/bin/ruff check apps/api
	@echo "==> Linting frontend..."
	npm --prefix apps/web run lint

format: ## Format backend code with Ruff
	@echo "==> Formatting backend..."
	apps/api/.venv/bin/ruff format apps/api

typecheck: ## Run static type checks for backend (mypy) and frontend (tsc)
	@echo "==> Typechecking backend..."
	apps/api/.venv/bin/mypy --config-file apps/api/pyproject.toml apps/api/app
	@echo "==> Typechecking frontend..."
	npm --prefix apps/web run typecheck

test-backend: ## Run backend unit and contract tests with pytest
	@echo "==> Running backend tests..."
	apps/api/.venv/bin/pytest -c apps/api/pyproject.toml apps/api/tests

test-frontend: ## Run frontend unit tests with Vitest
	@echo "==> Running frontend tests..."
	npm --prefix apps/web run test

test: test-backend test-frontend ## Run all test suites

migrate: ## Apply database migrations with Alembic
	@echo "==> Running database migrations..."
	apps/api/.venv/bin/alembic -c apps/api/alembic.ini upgrade head

seed: ## Seed database with deterministic development fixture data
	@echo "==> Seeding database..."
	apps/api/.venv/bin/python apps/api/scripts/seed_dev_data.py

check: lint typecheck test ## Run full local verification (lint, typecheck, tests)

