.PHONY: help build up down logs test lint scan deploy setup

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start local development environment
	docker-compose up -d

down: ## Stop local development environment
	docker-compose down

logs: ## View logs from all containers
	docker-compose logs -f

test: ## Run tests for API and Worker
	cd api && npm test
	# Add worker tests here

lint: ## Run linting
	cd api && npm run lint
	# Add worker linting here

scan: ## Run security scan using Trivy
	trivy fs .

deploy: ## Deploy to Kubernetes using Helm
	./scripts/deploy.sh

setup: ## Setup local environment
	./scripts/setup_env.sh
