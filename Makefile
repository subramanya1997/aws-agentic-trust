# Makefile for AWS Agentic Trust
# Usage: make [target]

# Variables
BACKEND_PORT := 8001
FRONTEND_PORT := 3000
BRIDGE_PORT := 8100

# Colors for terminal output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Help command
help:
	@echo "$(GREEN)AWS Agentic Trust Makefile$(NC)"
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "  $(GREEN)backend$(NC)      - Run the backend server (port $(BACKEND_PORT))"
	@echo "  $(GREEN)frontend$(NC)     - Run the frontend server (port $(FRONTEND_PORT))"
	@echo "  $(GREEN)bridge$(NC)       - Run the bridge server (port $(BRIDGE_PORT))"
	@echo "  $(GREEN)all$(NC)          - Run all services concurrently"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  $(GREEN)install$(NC)      - Install all dependencies"
	@echo "  $(GREEN)test$(NC)         - Run backend tests"
	@echo "  $(GREEN)format$(NC)       - Format backend code"
	@echo "  $(GREEN)lint$(NC)         - Lint backend code"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@echo "  $(GREEN)db-init$(NC)      - Initialize database"
	@echo "  $(GREEN)db-reset$(NC)     - Reset database"
	@echo ""
	@echo "$(YELLOW)Utils:$(NC)"
	@echo "  $(GREEN)clean$(NC)        - Clean build artifacts"
	@echo "  $(GREEN)stop$(NC)         - Stop all services"
	@echo "  $(GREEN)health$(NC)       - Check service health"

# Run services
backend:
	@echo "$(GREEN)Starting backend server...$(NC)"
	cd agentictrust && PYTHONPATH=. uv run uvicorn agentictrust.backend.main:app --reload --port $(BACKEND_PORT)

frontend:
	@echo "$(GREEN)Starting frontend server...$(NC)"
	cd agentictrust/frontend && npm run dev

bridge:
	@echo "$(GREEN)Starting bridge server...$(NC)"
	cd agentictrust && PYTHONPATH=. uv run python -m agentictrust.backend.bridge --transport sse --port $(BRIDGE_PORT)

all:
	@echo "$(GREEN)Starting all services...$(NC)"
	@make -j3 backend frontend bridge

# Development
install:
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	cd agentictrust && uv sync --all-extras
	cd agentictrust/frontend && npm install
	@echo "$(GREEN)Installation complete!$(NC)"

test:
	@echo "$(YELLOW)Running tests...$(NC)"
	cd agentictrust && PYTHONPATH=. uv run pytest -v

format:
	@echo "$(YELLOW)Formatting code...$(NC)"
	cd agentictrust && uv run black backend/
	cd agentictrust && uv run isort backend/

lint:
	@echo "$(YELLOW)Linting code...$(NC)"
	cd agentictrust && uv run flake8 backend/

# Database
db-init:
	@echo "$(YELLOW)Initializing database...$(NC)"
	cd agentictrust && PYTHONPATH=. uv run python -c "import asyncio; from agentictrust.backend.config.database import create_tables; asyncio.run(create_tables())"
	@echo "$(GREEN)Database initialized!$(NC)"

db-reset:
	@echo "$(RED)Resetting database...$(NC)"
	rm -f $$HOME/.agentictrust/db/*.db 2>/dev/null || true
	rm -f .agentictrust/db/*.db 2>/dev/null || true
	@echo "$(GREEN)Database reset!$(NC)"

# Utils
clean:
	@echo "$(RED)Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf agentictrust/frontend/.next 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

stop:
	@echo "$(RED)Stopping services...$(NC)"
	@pkill -f "uvicorn.*agentictrust.backend.main:app" || true
	@pkill -f "next dev" || true
	@pkill -f "agentictrust.backend.bridge" || true
	@echo "$(GREEN)All services stopped!$(NC)"

health:
	@echo "$(YELLOW)Checking service health...$(NC)"
	@curl -s http://localhost:$(BACKEND_PORT)/health > /dev/null && echo "$(GREEN)✓ Backend$(NC)" || echo "$(RED)✗ Backend$(NC)"
	@curl -s http://localhost:$(FRONTEND_PORT) > /dev/null && echo "$(GREEN)✓ Frontend$(NC)" || echo "$(RED)✗ Frontend$(NC)"
	@curl -s http://localhost:$(BRIDGE_PORT)/info > /dev/null && echo "$(GREEN)✓ Bridge$(NC)" || echo "$(RED)✗ Bridge$(NC)"

.PHONY: help backend frontend bridge all install test format lint db-init db-reset clean stop health 