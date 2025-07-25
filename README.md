# AWS Agentic Trust

A comprehensive gateway solution for managing and monitoring Model Context Protocol (MCP) interactions with built-in trust, security, and observability features.

## Overview

The Agentic Trust Gateway serves as a secure, observable, and trustworthy intermediary for AI agent interactions. It provides real-time monitoring, activity logging, trust scoring, and comprehensive management capabilities for MCP-based agent communications.

## Architecture

- **Backend**: FastAPI-based REST API with SQLAlchemy ORM
- **Frontend**: Next.js-based dashboard with real-time monitoring  
- **Bridge**: Agent-aware MCP protocol bridge for filtered multi-tenant access

## Key Features

### 🔒 Trust & Security
- Real-time trust scoring and validation
- Secure agent interaction monitoring
- Activity logging and audit trails
- Risk assessment and anomaly detection

### 📊 Observability
- Live system performance monitoring
- Detailed activity logs and event tracking
- Interactive dashboard with metrics visualization
- Comprehensive API documentation

### 🔧 Management
- MCP instance configuration and lifecycle management
- Registry for MCP server management
- Resource utilization tracking
- Error handling and recovery mechanisms
- User management and authentication

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- UV (fast Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:subramanya1997/aws-agentic-trust.git
   cd aws-agentic-trust
   ```

2. **Backend Setup**
   ```bash
   cd agentictrust
   uv sync --all-extras
   uv run uvicorn agentictrust.backend.main:app --reload --port 8001
   ```

3. **Frontend Setup**
   ```bash
   cd agentictrust/frontend
   npm install
   npm run dev
   ```

4. **Bridge Server (Optional)**
   ```bash
   cd agentictrust
   uv run python -m agentictrust.backend.bridge --transport sse --port 8100
   ```

5. **Access the Dashboard**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc
   - Bridge SSE: http://localhost:8100/sse

## Development

### Running Tests
```bash
cd agentictrust
uv run pytest
```

### Code Formatting
```bash
cd agentictrust
uv run black backend/
uv run isort backend/
```

### Linting
```bash
cd agentictrust
uv run flake8 backend/
```

### Using Make Commands
```bash
# Start all services
make all

# Start individual services
make backend      # Backend on port 8001
make frontend     # Frontend on port 3000
make bridge       # Bridge on port 8100

# Development mode
make dev-backend
make dev-frontend
make dev-bridge

# Install dependencies
make install

# Database operations
make db-reset
make backend-db-init

# Code quality
make format-backend
make lint-backend
make test-backend

# Health check
make health-check
```

## Project Structure

```
├── agentictrust/              # Main application
│   ├── backend/               # FastAPI backend service
│   │   ├── api/               # REST API endpoints
│   │   ├── bridge/            # Agent-aware MCP bridge
│   │   ├── config/            # Configuration management
│   │   ├── core/              # Core business logic
│   │   ├── data/              # Data models and database
│   │   ├── schemas/           # Pydantic schemas
│   │   └── scripts/           # Utility scripts
│   ├── frontend/              # Next.js dashboard
│   │   ├── src/app/           # Next.js app router
│   │   ├── src/components/    # React components
│   │   └── public/            # Static assets
│   ├── pyproject.toml         # Python dependencies
│   └── uv.lock               # Dependency lock file
├── Makefile                   # Development commands
└── README.md                  # This file
```

## API Endpoints

The backend provides RESTful APIs for:

- **MCP Registry**: `/api/v1/registry` - MCP server management
- **MCP Instances**: `/api/v1/mcp-instances` - Instance configuration
- **Users**: `/api/v1/users` - User management
- **Capabilities**: `/api/v1/capabilities` - Capability discovery
- **Logs**: `/api/v1/logs` - Activity monitoring
- **Usage Stats**: `/api/v1/usage` - Usage analytics
- **Bridge**: `/api/v1/bridge` - MCP bridge endpoints

## Bridge Server

The bridge server provides multi-tenant MCP access with per-agent filtering:

- Authenticates agents via HTTP Basic auth
- Filters tools, resources, and prompts based on agent permissions
- Supports SSE, stdio, and HTTP transports
- Aggregates multiple upstream MCP servers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run code formatting and linting
6. Submit a pull request

## License

MIT License

---

Built with ❤️ for secure and trustworthy AI agent interactions. 