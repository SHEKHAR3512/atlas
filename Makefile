.PHONY: help setup up down restart logs migrate seed test lint format paper backtest research live-preflight kill backup restore

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
NPM ?= npm

help:
	@echo "ATLAS Autonomous Trading & Learning Agent System"
	@echo "Available commands:"
	@echo "  make setup          - Initialize environment, virtualenv, and install dependencies"
	@echo "  make up             - Start all services (API, Dashboard, Database, Monitoring)"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart services"
	@echo "  make logs           - Tail service logs"
	@echo "  make migrate        - Run database migrations"
	@echo "  make seed           - Seed initial market data and approved strategies"
	@echo "  make test           - Run full test suite (unit, integration, risk, execution)"
	@echo "  make lint           - Run code linter"
	@echo "  make format         - Autoformat code"
	@echo "  make paper          - Start autonomous paper trading daemon"
	@echo "  make backtest       - Run strategy backtests across benchmark data"
	@echo "  make research       - Run Autonomous Research Lab experiment queue"
	@echo "  make live-preflight - Run strict preflight safety checks for live trading"
	@echo "  make kill           - Trigger Emergency Hard Kill Switch (fail-closed)"
	@echo "  make backup         - Create database snapshot backup"
	@echo "  make restore        - Restore database snapshot (usage: make restore FILE=path)"

setup:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi
	@if [ ! -d .venv ]; then python3 -m venv .venv && echo "Created .venv"; fi
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install -r services/atlas/requirements.txt
	@cd apps/web && $(NPM) install
	@echo "Setup complete. Run 'make migrate' then 'make seed' then 'make up'."

up:
	@if docker info >/dev/null 2>&1; then \
		docker compose up -d --build; \
		echo "Services started via Docker Compose:"; \
		echo "  Dashboard: http://localhost:3000"; \
		echo "  FastAPI:   http://localhost:8000"; \
		echo "  Docs:      http://localhost:8000/docs"; \
		echo "  Grafana:   http://localhost:3001"; \
	else \
		echo "Docker daemon not accessible; launching native local services..."; \
		mkdir -p logs; \
		$(PYTHON) -m services.atlas.main > logs/api.log 2>&1 & echo $$! > .api.pid; \
		cd apps/web && $(NPM) run dev > ../../logs/web.log 2>&1 & echo $$! > ../../.web.pid; \
		echo "Native services started in background:"; \
		echo "  Dashboard: http://localhost:3000 (logs/web.log)"; \
		echo "  FastAPI:   http://localhost:8000 (logs/api.log)"; \
	fi

down:
	@if docker info >/dev/null 2>&1; then \
		docker compose down; \
	fi
	@if [ -f .api.pid ]; then kill `cat .api.pid` 2>/dev/null || true; rm -f .api.pid; fi
	@if [ -f .web.pid ]; then kill `cat .web.pid` 2>/dev/null || true; rm -f .web.pid; fi
	@pkill -f "uvicorn services.atlas.main:app" 2>/dev/null || true
	@pkill -f "next-server" 2>/dev/null || true
	@echo "Services stopped."

restart: down up

logs:
	@if docker info >/dev/null 2>&1; then \
		docker compose logs -f; \
	else \
		tail -f logs/api.log logs/web.log 2>/dev/null; \
	fi

migrate:
	@$(PYTHON) -m services.atlas.db.migrate

seed:
	@$(PYTHON) -m services.atlas.data.seed

test:
	@$(PYTHON) -m pytest tests/ -v

lint:
	@$(PYTHON) -m pip install ruff >/dev/null 2>&1 || true
	@ruff check services/ tests/

format:
	@$(PYTHON) -m pip install ruff >/dev/null 2>&1 || true
	@ruff format services/ tests/

paper:
	@$(PYTHON) -m services.atlas.workers.paper_trader

backtest:
	@$(PYTHON) -m services.atlas.backtesting.runner

research:
	@$(PYTHON) -m services.atlas.research.runner

live-preflight:
	@$(PYTHON) -m services.atlas.core.preflight

kill:
	@$(PYTHON) -m services.atlas.risk.circuit_breaker --kill

backup:
	@mkdir -p backups
	@$(PYTHON) -m services.atlas.db.backup create

restore:
	@if [ -z "$(FILE)" ]; then echo "Error: FILE argument is required. Usage: make restore FILE=backups/snapshot.sql"; exit 1; fi
	@$(PYTHON) -m services.atlas.db.backup restore $(FILE)
