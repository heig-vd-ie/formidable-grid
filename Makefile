# Specific Makefile for the project {{PROJECT_NAME}}
include Makefile.common.mak

COMPOSE_FILE ?= docker-compose.yml

build: ## Build the Docker images
	docker compose -f $(COMPOSE_FILE) build

_start: ## Start the Docker containers
	docker compose -f $(COMPOSE_FILE) up -d

start: ## Build and start the Docker containers
	@$(MAKE) build
	@$(MAKE) _start

stop: ## Stop the Docker containers
	docker compose -f $(COMPOSE_FILE) stop

down: ## Stop and remove the Docker containers
	docker compose -f $(COMPOSE_FILE) down

restart: ## Restart the Docker containers
	@$(MAKE) stop
	@$(MAKE) _start

logs: ## View the logs for the Docker containers
	docker compose -f $(COMPOSE_FILE) logs -f
