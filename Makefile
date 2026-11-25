# Comandos principales. Requiere Docker con Compose v2.
COMPOSE = docker compose
API = apps/api
DASH = apps/dashboard

.PHONY: help env dev down logs migrate seed test lint lint-api lint-dash typecheck key reset

help: ## Lista los comandos
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

key: ## Genera una clave Fernet
	@openssl rand -base64 32 | tr '+/' '-_'

env: ## Crea .env desde .env.example con claves nuevas
	@if [ -f .env ]; then echo ".env ya existe, no lo toco."; else \
		cp .env.example .env && \
		perl -pi -e "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$$(openssl rand -base64 32 | tr '+/' '-_')|" .env && \
		perl -pi -e "s|^N8N_ENCRYPTION_KEY=.*|N8N_ENCRYPTION_KEY=$$(openssl rand -hex 24)|" .env && \
		echo ".env creado."; fi

dev: env ## Levanta todo (http://localhost)
	$(COMPOSE) up -d --build
	@echo "Panel: http://localhost  ·  Mails: http://localhost:8025  ·  n8n: http://localhost:5678"

down: ## Apaga todo
	$(COMPOSE) down

reset: ## Apaga todo y borra los datos
	$(COMPOSE) down -v

logs: ## Sigue los logs de la API y el worker
	$(COMPOSE) logs -f api worker

migrate: ## Corre las migraciones
	$(COMPOSE) run --rm migrate

seed: ## Crea un operador y un negocio de ejemplo
	$(COMPOSE) run --rm migrate python -m app.seed

test: ## Tests de la API contra el Postgres del compose
	$(COMPOSE) up -d --wait postgres redis
	cd $(API) && uv run pytest

lint: lint-api lint-dash typecheck ## Lint y tipos de todo

lint-api:
	cd $(API) && uv run ruff check . && uv run ruff format --check . && uv run mypy app

lint-dash:
	cd $(DASH) && pnpm lint

typecheck:
	cd $(DASH) && pnpm typecheck
