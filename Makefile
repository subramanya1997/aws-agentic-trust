# Makefile for running simple_mcp services
# Usage: make [target]

# Variables
PYTHON := python3
NPM := npm
BACKEND_PORT := 8001
FRONTEND_PORT := 3000
PROXY_PORT := 8000
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
	@echo "$(GREEN)Simple MCP Services Makefile$(NC)"
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "  $(GREEN)backend$(NC)      - Run the backend server (FastAPI on port $(BACKEND_PORT))"
	@echo "  $(GREEN)frontend$(NC)     - Run the frontend server (Next.js on port $(FRONTEND_PORT))"
	@echo "  $(GREEN)proxy$(NC)        - Run the proxy server (MCP Proxy on port $(PROXY_PORT))"
	@echo "  $(GREEN)bridge$(NC)       - Run the bridge server (Agent-Aware MCP Bridge on port $(BRIDGE_PORT))"
	@echo "  $(GREEN)all$(NC)          - Run all services concurrently"
	@echo ""
	@echo "$(YELLOW)Installation:$(NC)"
	@echo "  $(GREEN)install$(NC)      - Install dependencies for all services"
	@echo "  $(GREEN)install-backend$(NC) - Install backend dependencies with UV"
	@echo "  $(GREEN)install-frontend$(NC) - Install frontend dependencies"
	@echo "  $(GREEN)uv-update$(NC)    - Update backend dependencies with UV"
	@echo "  $(GREEN)uv-venv$(NC)      - Create UV virtual environment"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  $(GREEN)dev-backend$(NC)  - Run backend in development mode with debug logging"
	@echo "  $(GREEN)dev-frontend$(NC) - Run frontend in development mode"
	@echo "  $(GREEN)dev-bridge$(NC)   - Run bridge in development mode with debug logging"
	@echo "  $(GREEN)test-backend$(NC) - Run backend tests"
	@echo "  $(GREEN)format-backend$(NC) - Format backend code with black and isort"
	@echo "  $(GREEN)lint-backend$(NC) - Lint backend code with flake8"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@echo "  $(GREEN)backend-db-init$(NC) - Initialize backend database tables"
	@echo "  $(GREEN)db-reset$(NC)    - Reset all databases"
	@echo ""
	@echo "$(YELLOW)Operations:$(NC)"
	@echo "  $(GREEN)clean$(NC)        - Clean build artifacts and caches"
	@echo "  $(GREEN)logs$(NC)         - Show logs from all services"
	@echo "  $(GREEN)stop$(NC)         - Stop all running services"
	@echo "  $(GREEN)health-check$(NC) - Check health of all services"

# Run backend server
backend:
	@echo "$(GREEN)Starting backend server on port $(BACKEND_PORT)...$(NC)"
	cd agentictrust && PYTHONPATH=.. uv run uvicorn agentictrust.backend.main:app --reload --port $(BACKEND_PORT)

# Run frontend server
frontend:
	@echo "$(GREEN)Starting frontend server on port $(FRONTEND_PORT)...$(NC)"
	cd agentictrust/frontend && $(NPM) run dev

# Run proxy server
proxy:
	@echo "$(GREEN)Starting proxy server...$(NC)"
	cd agentictrust && PYTHONPATH=.. PROXY_TRANSPORT=sse AGENTICTRUST_SERVER_URL=http://localhost:$(BACKEND_PORT) uv run python ../examples/start_proxy_server.py

# Run bridge server
bridge:
	@echo "$(GREEN)Starting bridge server on port $(BRIDGE_PORT)...$(NC)"
	cd agentictrust && PYTHONPATH=.. uv run python -m agentictrust.backend.bridge --transport sse --port $(BRIDGE_PORT)

# Run all services concurrently
all:
	@echo "$(GREEN)Starting all services...$(NC)"
	@echo "$(YELLOW)Note: This will run all services in parallel. Use Ctrl+C to stop all.$(NC)"
	@make -j4 backend frontend proxy bridge

# Install all dependencies
install: install-backend install-frontend
	@echo "$(GREEN)All dependencies installed successfully!$(NC)"

# Install backend dependencies
install-backend:
	@echo "$(YELLOW)Installing backend dependencies with UV...$(NC)"
	cd agentictrust && uv sync --all-extras

# Install frontend dependencies
install-frontend:
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	cd agentictrust/frontend && $(NPM) install

# Clean build artifacts and caches
clean:
	@echo "$(RED)Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf agentictrust/frontend/.next 2>/dev/null || true
	rm -rf agentictrust/frontend/node_modules 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

# Show logs (basic implementation - can be extended)
logs:
	@echo "$(YELLOW)Showing recent logs...$(NC)"
	@if [ -f .agentictrust/db/agentictrust.db ]; then \
		echo "$(GREEN)Backend database exists$(NC)"; \
	fi
	@if [ -f .proxy/db/proxy.db ]; then \
		echo "$(GREEN)Proxy database exists$(NC)"; \
	fi

# Stop all services
stop:
	@echo "$(RED)Stopping all services...$(NC)"
	@pkill -f "uvicorn.*agentictrust.backend.main:app" || true
	@pkill -f "next dev" || true
	@pkill -f "start_proxy_server.py" || true
	@pkill -f "agentictrust.backend.bridge" || true
	@echo "$(GREEN)All services stopped!$(NC)"

# Development targets with specific configurations
dev-backend:
	@echo "$(GREEN)Starting backend in development mode with auto-reload...$(NC)"
	cd agentictrust && PYTHONPATH=.. ENVIRONMENT=development DEBUG=true uv run uvicorn agentictrust.backend.main:app --reload --port $(BACKEND_PORT) --log-level debug

dev-frontend:
	@echo "$(GREEN)Starting frontend in development mode with turbopack...$(NC)"
	cd agentictrust/frontend && $(NPM) run dev

dev-proxy:
	@echo "$(GREEN)Starting proxy in development mode...$(NC)"
	cd agentictrust && PYTHONPATH=.. PROXY_TRANSPORT=sse AGENTICTRUST_SERVER_URL=http://localhost:$(BACKEND_PORT) uv run python ../examples/start_proxy_server.py

dev-bridge:
	@echo "$(GREEN)Starting bridge in development mode with debug logging...$(NC)"
	cd agentictrust && PYTHONPATH=.. uv run python -m agentictrust.backend.bridge --transport sse --port $(BRIDGE_PORT) --log-level DEBUG

# Production targets
prod-backend:
	@echo "$(GREEN)Starting backend in production mode...$(NC)"
	cd agentictrust && PYTHONPATH=.. ENVIRONMENT=production uv run uvicorn agentictrust.backend.main:app --host 0.0.0.0 --port $(BACKEND_PORT) --workers 4

prod-frontend:
	@echo "$(GREEN)Building and starting frontend in production mode...$(NC)"
	cd agentictrust/frontend && $(NPM) run build && $(NPM) run start

# Database management
db-reset:
	@echo "$(RED)Resetting databases...$(NC)"
	# Remove backend DB in user home (~/.agentictrust)
	rm -f $$HOME/.agentictrust/db/*.db 2>/dev/null || true
	# Remove any local project DB (proxy default location)
	rm -f .agentictrust/db/*.db 2>/dev/null || true
	# Remove backup copies if any
	rm -f $$HOME/.agentictrust/backups/*.db 2>/dev/null || true
	rm -f .agentictrust/backups/*.db 2>/dev/null || true
	@echo "$(GREEN)Databases reset!$(NC)"

# Backend-specific database operations
backend-db-init:
	@echo "$(YELLOW)Initializing backend database...$(NC)"
	cd agentictrust && PYTHONPATH=.. ENVIRONMENT=development uv run python -c "import asyncio; from agentictrust.backend.config.database import create_tables; asyncio.run(create_tables())"
	@echo "$(GREEN)Backend database initialized!$(NC)"

# Backend testing
test-backend:
	@echo "$(YELLOW)Running backend tests...$(NC)"
	cd agentictrust && PYTHONPATH=.. uv run pytest -v

# Backend code formatting and linting
format-backend:
	@echo "$(YELLOW)Formatting backend code...$(NC)"
	cd agentictrust && uv run black backend/
	cd agentictrust && uv run isort backend/

lint-backend:
	@echo "$(YELLOW)Linting backend code...$(NC)"
	cd agentictrust && uv run flake8 backend/

# UV-specific commands
uv-update:
	@echo "$(YELLOW)Updating backend dependencies with UV...$(NC)"
	cd agentictrust && uv sync --upgrade
	@echo "$(GREEN)Dependencies updated!$(NC)"

uv-venv:
	@echo "$(YELLOW)Creating UV virtual environment...$(NC)"
	cd agentictrust && uv venv
	@echo "$(GREEN)Virtual environment created! Activate with: source .venv/bin/activate$(NC)"

uv-show:
	@echo "$(YELLOW)Showing installed dependencies...$(NC)"
	cd agentictrust && uv pip list

uv-env-info:
	@echo "$(YELLOW)UV environment information:$(NC)"
	cd agentictrust && uv python list

# Health checks
health-check:
	@echo "$(YELLOW)Checking service health...$(NC)"
	@curl -s http://localhost:$(BACKEND_PORT)/health > /dev/null && echo "$(GREEN)✓ Backend is healthy$(NC)" || echo "$(RED)✗ Backend is not responding$(NC)"
	@curl -s http://localhost:$(FRONTEND_PORT) > /dev/null && echo "$(GREEN)✓ Frontend is healthy$(NC)" || echo "$(RED)✗ Frontend is not responding$(NC)"
	@curl -s http://localhost:$(PROXY_PORT)/logs > /dev/null && echo "$(GREEN)✓ Proxy is healthy$(NC)" || echo "$(RED)✗ Proxy is not responding$(NC)"
	@curl -s http://localhost:$(BRIDGE_PORT) > /dev/null && echo "$(GREEN)✓ Bridge is healthy$(NC)" || echo "$(RED)✗ Bridge is not responding$(NC)"

# Docker targets (if needed in future)
docker-build:
	@echo "$(YELLOW)Docker support not yet implemented$(NC)"

docker-up:
	@echo "$(YELLOW)Docker support not yet implemented$(NC)"

docker-down:
	@echo "$(YELLOW)Docker support not yet implemented$(NC)"

.PHONY: help backend frontend proxy bridge all install install-backend install-frontend clean logs stop \
        dev-backend dev-frontend dev-proxy dev-bridge prod-backend prod-frontend db-reset health-check \
        backend-db-init test-backend format-backend lint-backend \
        uv-update uv-venv uv-show uv-env-info \
        docker-build docker-up docker-down 