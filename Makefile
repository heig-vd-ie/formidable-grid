# Specific Makefile for the project {{PROJECT_NAME}}
include Makefile.common.mak

COMPOSE_FILE ?= docker-compose.yml

fetch-images: ## Fetch the Docker images
	@. ./scripts/fetch-images.sh

build: ## Build the Docker images
	cd dockerfiles && docker compose -f $(COMPOSE_FILE) -p formidable-grid build && cd ..

_start: ## Start the Docker containers
	cd dockerfiles && docker compose -f $(COMPOSE_FILE) -p formidable-grid up -d $(CONTAINERS) && cd ..

start: ## Start Native service frontend (the docker should be first stopped)
	@./scripts/start-dev.sh

stop: ## Stop the Docker containers
	cd dockerfiles && docker compose -f $(COMPOSE_FILE) -p formidable-grid stop && cd ..

down: ## Stop and remove the Docker containers
	cd dockerfiles && docker compose -f $(COMPOSE_FILE) -p formidable-grid down && cd ..

restart: ## Restart the Docker containers
	@$(MAKE) stop _start

logs: ## View the logs for the Docker containers
	cd dockerfiles && docker compose -f $(COMPOSE_FILE) -p formidable-grid logs -f $(CONTAINERS)

kill-port: ## Kill any process running on the specified port
	@if lsof -ti :"$(PORT)" >/dev/null; then \
		echo "🔪 Killing process on port $(PORT)..."; \
		kill -9 $$(lsof -ti :"$(PORT)"); \
	fi
