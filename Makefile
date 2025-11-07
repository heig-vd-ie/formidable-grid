# Specific Makefile for the project {{PROJECT_NAME}}
include Makefile.common.mak

COMPOSE_FILE ?= docker-compose.yml

fetch-images: ## Fetch the Docker images
	@. ./scripts/fetch-images.sh

build: ## Build the Docker images
	docker compose -f $(COMPOSE_FILE) build

_start: ## Start the Docker containers
	docker compose -f $(COMPOSE_FILE) up -d $(CONTAINERS)

start: ## Start Native service frontend (the docker should be first stopped)
	@./scripts/start-dev.sh

stop: ## Stop the Docker containers
	docker compose -f $(COMPOSE_FILE) stop

down: ## Stop and remove the Docker containers
	docker compose -f $(COMPOSE_FILE) down

restart: ## Restart the Docker containers
	@$(MAKE) stop _start

logs: ## View the logs for the Docker containers
	docker compose -f $(COMPOSE_FILE) logs -f $(CONTAINERS)

kill-port: ## Kill any process running on the specified port
	@if lsof -ti :"$(PORT)" >/dev/null; then \
		echo "🔪 Killing process on port $(PORT)..."; \
		kill -9 $$(lsof -ti :"$(PORT)"); \
	fi
