.PHONY: help setup up down restart logs clean test

help: ## Show this help message
	@echo "Finance Analytics & Trading Co-Pilot - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup - creates env file and directories
	@echo "Setting up project..."
	@./quickstart.sh

up: ## Start all services
	@echo "Starting all services..."
	@docker-compose up -d
	@echo "✓ Services started"
	@echo "Dashboard: http://localhost:8501"
	@echo "API Docs:  http://localhost:8000/docs"

down: ## Stop all services
	@echo "Stopping all services..."
	@docker-compose down
	@echo "✓ Services stopped"

restart: ## Restart all services
	@echo "Restarting services..."
	@docker-compose restart
	@echo "✓ Services restarted"

logs: ## Show logs from all services
	@docker-compose logs -f

logs-api: ## Show FastAPI logs
	@docker-compose logs -f fastapi

logs-dashboard: ## Show Streamlit logs
	@docker-compose logs -f streamlit

logs-kafka: ## Show Kafka logs
	@docker-compose logs -f kafka

logs-spark: ## Show Spark logs
	@docker-compose logs -f spark-master spark-worker

logs-producers: ## Show data producers logs
	@docker-compose logs -f data-producers

status: ## Check status of all services
	@docker-compose ps

clean: ## Remove all containers, volumes, and generated files
	@echo "⚠️  This will remove all data and containers. Are you sure? [y/N]"
	@read -r response; \
	if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
		echo "Cleaning up..."; \
		docker-compose down -v; \
		rm -rf backend/logs/*; \
		rm -rf spark/data/checkpoints/*; \
		rm -rf airflow/logs/*; \
		echo "✓ Cleanup complete"; \
	else \
		echo "Cancelled"; \
	fi

build: ## Rebuild all Docker images
	@echo "Rebuilding Docker images..."
	@docker-compose build --no-cache
	@echo "✓ Build complete"

test: ## Run backend tests
	@echo "Running tests..."
	@docker-compose exec fastapi pytest -v
	@echo "✓ Tests complete"

shell-api: ## Open shell in FastAPI container
	@docker-compose exec fastapi /bin/bash

shell-spark: ## Open shell in Spark master container
	@docker-compose exec spark-master /bin/bash

db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	@docker-compose exec fastapi alembic upgrade head
	@echo "✓ Migrations complete"

grafana-import: ## Import Grafana dashboards
	@echo "Importing Grafana dashboards..."
	@curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
		-H "Content-Type: application/json" \
		-d @monitoring/grafana/dashboards/main-dashboard.json
	@echo "✓ Dashboards imported"

backup-db: ## Backup PostgreSQL database
	@echo "Backing up database..."
	@docker-compose exec postgres pg_dump -U financeuser financedb > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✓ Database backed up"

restore-db: ## Restore PostgreSQL database (use: make restore-db FILE=backup.sql)
	@echo "Restoring database from $(FILE)..."
	@docker-compose exec -T postgres psql -U financeuser financedb < $(FILE)
	@echo "✓ Database restored"

install-dev: ## Install development dependencies
	@echo "Installing development dependencies..."
	@pip install -r backend/requirements.txt
	@pip install -r frontend/requirements.txt
	@echo "✓ Dependencies installed"

format: ## Format Python code with black
	@echo "Formatting code..."
	@black backend/app
	@black frontend/app.py
	@echo "✓ Code formatted"

lint: ## Lint Python code with flake8
	@echo "Linting code..."
	@flake8 backend/app
	@flake8 frontend/app.py
	@echo "✓ Linting complete"

docs: ## Generate API documentation
	@echo "Generating documentation..."
	@cd backend && python -m pdoc --html --output-dir ../docs app
	@echo "✓ Documentation generated in docs/"

docker-prune: ## Remove unused Docker resources
	@echo "Pruning Docker resources..."
	@docker system prune -f
	@echo "✓ Docker pruned"

check-health: ## Check health of all services
	@echo "Checking service health..."
	@echo "FastAPI:    $(shell curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"
	@echo "Streamlit:  $(shell curl -s -o /dev/null -w '%{http_code}' http://localhost:8501)"
	@echo "Grafana:    $(shell curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/api/health)"
	@echo "MLflow:     $(shell curl -s -o /dev/null -w '%{http_code}' http://localhost:5000)"
	@echo "Postgres:   $(shell docker-compose exec postgres pg_isready -U financeuser > /dev/null 2>&1 && echo 'OK' || echo 'DOWN')"
