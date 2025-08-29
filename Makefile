# Specific Makefile for the project {{PROJECT_NAME}}
include Makefile.common.mak

COMPOSE_FILE ?= docker-compose.yml
NATIVE_SERVICES ?= backend-arras-api
ALL_SERVICES := $(shell docker compose -f $(COMPOSE_FILE) config --services)
ONLY_DOCKER_SERVICES := $(filter-out $(NATIVE_SERVICES),$(ALL_SERVICES))

fetch-images: ## Fetch the Docker images
	@. ./scripts/fetch-images.sh

build: ## Build the Docker images
	docker compose -f $(COMPOSE_FILE) build

_start: ## Start the Docker containers
	docker compose -f $(COMPOSE_FILE) up -d $(DOCKER_SERVICES)

start: ## Build and start the Docker containers
	@$(MAKE) build
	@for svc in $(ALL_SERVICES); do \
		$(MAKE) _start DOCKER_SERVICES=$$svc; \
	done
	$(MAKE) logs

start-dev: ## Build and start the Docker containers in development mode
	@./scripts/run-native-all.sh

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