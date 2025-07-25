# Agentic Trust Gateway

A comprehensive gateway solution for managing and monitoring Model Context Protocol (MCP) interactions with built-in trust, security, and observability features.

## Overview

The Agentic Trust Gateway serves as a secure, observable, and trustworthy intermediary for AI agent interactions. It provides real-time monitoring, activity logging, trust scoring, and comprehensive management capabilities for MCP-based agent communications.

## Architecture

- **Backend**: FastAPI-based REST API with SQLAlchemy ORM
- **Frontend**: Next.js-based dashboard with real-time monitoring
- **Bridge**: MCP protocol bridge for seamless integration
- **Proxy**: Intelligent routing and security layer

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
- Agent configuration and lifecycle management
- Resource utilization tracking
- Error handling and recovery mechanisms
- Scalable deployment options

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- UV (fast Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd simple_mcp
   ```

2. **Backend Setup**
   ```bash
   cd agentictrust
   uv sync --all-extras
   uv run uvicorn agentictrust.backend.main:app --reload --port 8000
   ```

3. **Frontend Setup**
   ```bash
   cd agentictrust/frontend
   npm install
   npm run dev
   ```

4. **Access the Dashboard**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Development

### Running Tests
```bash
cd agentictrust
uv run pytest
```

### Code Formatting
```bash
uv run black .
uv run isort .
```

### Linting
```bash
uv run flake8 .
```

## Project Structure

```
├── agentictrust/          # Main application
│   ├── backend/           # FastAPI backend service
│   ├── frontend/          # Next.js dashboard
│   └── tests/             # Test suite
├── proxy/                 # MCP proxy layer
├── examples/              # Usage examples
└── docs/                  # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License

---

Built with ❤️ for secure and trustworthy AI agent interactions. 