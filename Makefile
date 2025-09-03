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

start-dev: ## Start Native service GLM plotter (the docker should be first stopped)
	@export DEV=true && \
		cd frontend-gridlabd/glm-plotter && \
		python glm-plotter.py

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

fix-permission: ## Fix permissions for the uploads and models directories
	@echo "Fixing permissions for uploads and models directories"
	@sudo mkdir -p $(UPLOADS_FOLDER_NATIVE) $(MODELS_FOLDER_NATIVE)
	@sudo chown -R $$(whoami):$(whoami) $(UPLOADS_FOLDER_NATIVE) $(MODELS_FOLDER_NATIVE)
	@sudo chmod -R 755 $(UPLOADS_FOLDER_NATIVE) $(MODELS_FOLDER_NATIVE)