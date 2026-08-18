.PHONY: help dev dev-docker stop logs test test-python test-rust lint typecheck build clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start API in development mode (local)
	python -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000

dev-docker: ## Start all services via Docker Compose
	docker compose up -d --build

stop: ## Stop all Docker services
	docker compose down

logs: ## Tail Docker logs
	docker compose logs -f

test: test-python test-rust ## Run all tests

test-python: ## Run Python tests
	python -m pytest tests/ -v

test-rust: ## Run Rust tests
	cargo test --manifest-path rust/finintel-engine/Cargo.toml

lint: ## Run linting (Python + Rust)
	ruff check apps/ tests/
	cargo clippy --manifest-path rust/finintel-engine/Cargo.toml -- -D warnings

typecheck: ## Run type checking
	mypy apps/

build: ## Build Rust engine
	cargo build --manifest-path rust/finintel-engine/Cargo.toml --release

clean: ## Clean build artifacts
	cargo clean --manifest-path rust/finintel-engine/Cargo.toml
	Remove-Item -Recurse -Force -ErrorAction SilentlyContinue __pycache__, .pytest_cache, .mypy_cache, .ruff_cache
