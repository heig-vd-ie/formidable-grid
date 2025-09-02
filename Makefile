# Specific Makefile for the project {{PROJECT_NAME}}
include Makefile.common.mak

COMPOSE_FILE ?= docker-compose.yml

fetch-images: ## Fetch the Docker images
	@. ./scripts/fetch-images.sh

_build: ## Build the Docker images
	docker compose -f $(COMPOSE_FILE) build

_start: ## Start the Docker containers
	docker compose -f $(COMPOSE_FILE) up -d $(CONTAINERS)

start: ## Build and start the Docker containers
	@$(MAKE) _build
	@$(MAKE) _start
	$(MAKE) logs

start-dev: ## Start Native service GLM plotter (the docker should be first stopped)
	@cd frontend-glmplotter/glm-plotter && \
		python glm-plotter.py

stop: ## Stop the Docker containers
	docker compose -f $(COMPOSE_FILE) stop

down: ## Stop and remove the Docker containers
	docker compose -f $(COMPOSE_FILE) down

restart: ## Restart the Docker containers
	@$(MAKE) stop _start

logs: ## View the logs for the Docker containers
	docker compose -f $(COMPOSE_FILE) logs -f

kill-port: ## Kill any process running on the specified port
	@if lsof -ti :"$(PORT)" >/dev/null; then \
		echo "🔪 Killing process on port $(PORT)..."; \
		kill -9 $$(lsof -ti :"$(PORT)"); \
	fi
