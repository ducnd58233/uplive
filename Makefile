BACKEND_DIR := backend
ROOT_COMPOSE := deployments/docker/docker-compose.yml
BACKEND_COMPOSE := backend/deployments/docker/docker-compose.yml
INFRA_COMPOSE := backend/deployments/docker/docker-compose.infra.yml
FRONTEND_COMPOSE := frontend/deployments/docker/docker-compose.yml

UV ?= $(if $(filter Windows_NT,$(OS)),python -m uv,uv)
PYTHON ?= python
COMPOSE ?= docker compose

.DEFAULT_GOAL := help

.PHONY: help create sync up down up-backend down-backend up-infra down-infra \
	run-api run-worker test lint \
	migrate migrate-down migration migration-up migration-down

help:
	@echo "uplive — available targets"
	@echo ""
	@echo "  Setup"
	@echo "    make create          Create/update conda env and install deps (uv sync)"
	@echo "    make sync            Install backend deps only (uv sync)"
	@echo ""
	@echo "  Docker"
	@echo "    make up              Full stack up (--build)"
	@echo "    make down            Full stack down (-v)"
	@echo "    make up-backend      Backend only (redis, postgres, api, worker)"
	@echo "    make down-backend    Backend down (-v)"
	@echo "    make up-infra        Infra only (redis, postgres)"
	@echo "    make down-infra      Infra down (-v)"
	@echo ""
	@echo "  Run (local, from backend — infra must be up)"
	@echo "    make run-api         Uvicorn API on :8000"
	@echo "    make run-worker      arq worker"
	@echo ""
	@echo "  Migrations (Alembic, run from backend/)"
	@echo "    make migrate         Apply all migrations (upgrade head)"
	@echo "    make migrate-down    Roll back one migration"
	@echo "    make migration MSG=name   Create new migration revision"
	@echo ""
	@echo "  Quality"
	@echo "    make test            pytest"
	@echo "    make lint            ruff check + format"

create:
	cd $(BACKEND_DIR) && conda env create -f environment.yml || conda env update -f environment.yml --prune
	cd $(BACKEND_DIR) && $(UV) sync

sync:
	cd $(BACKEND_DIR) && $(UV) sync

up:
	$(COMPOSE) -f $(ROOT_COMPOSE) up --build

down:
	$(COMPOSE) -f $(ROOT_COMPOSE) down -v

up-backend:
	$(COMPOSE) -f $(BACKEND_COMPOSE) up --build

down-backend:
	$(COMPOSE) -f $(BACKEND_COMPOSE) down -v

up-infra:
	$(COMPOSE) -f $(INFRA_COMPOSE) up -d

down-infra:
	$(COMPOSE) -f $(INFRA_COMPOSE) down -v

run-api:
	cd $(BACKEND_DIR) && $(UV) run uvicorn app.main:app --reload --port 8000

run-worker:
	cd $(BACKEND_DIR) && $(UV) run arq app.worker.WorkerSettings

migrate migration-up:
	cd $(BACKEND_DIR) && $(UV) run alembic upgrade head

migrate-down migration-down:
	cd $(BACKEND_DIR) && $(UV) run alembic downgrade -1

migration:
ifndef MSG
	$(error MSG is required. Example: make migration MSG=add_user_table)
endif
	cd $(BACKEND_DIR) && $(UV) run alembic revision -m "$(MSG)"

test:
	cd $(BACKEND_DIR) && $(UV) run pytest

test-integration:
	cd $(BACKEND_DIR) && $(UV) run pytest -m integration

lint:
	cd $(BACKEND_DIR) && $(UV) run ruff check .
	cd $(BACKEND_DIR) && $(UV) run ruff format .
