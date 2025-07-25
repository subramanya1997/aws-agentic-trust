# AgenticTrust Backend - Production-Ready Architecture

## 🎯 Overview

The AgenticTrust backend has been completely refactored into a modern, production-ready FastAPI application with best-in-class architecture patterns.

## 🏗️ Architecture

### **Folder Structure**
```
agentictrust/backend/
├── main.py                 # FastAPI app entry point
├── config/
│   ├── settings.py         # Environment-based configuration
│   └── database.py         # Database configuration
├── api/
│   ├── dependencies.py     # Dependency injection
│   └── v1/
│       ├── router.py       # Main API router
│       └── endpoints/
│           ├── health.py   # Health checks
│           ├── upstreams.py # MCP server management
│           └── logs.py     # Logging endpoints
├── core/
│   ├── exceptions.py       # Custom exceptions
│   ├── middleware.py       # Custom middleware
│   └── logging.py          # Structured logging
├── schemas/
│   ├── upstream.py        # Pydantic schemas
│   ├── logs.py
│   └── responses.py       # Standard response schemas
└── README.md              # This file
```

### **Data Layer Structure**
```
agentictrust/data/
├── models/
│   ├── base.py            # SQLAlchemy base models
│   ├── upstream.py        # ORM models
│   ├── logs.py
│   └── observability.py
├── paths.py               # Database paths
├── sqlite.py              # Legacy SQLite support
└── schema.sql             # SQL schema
```

## 🚀 Key Features

### **1. Multi-Database Support**
- **SQLite** for development (automatic)
- **PostgreSQL** for production (via environment variables)
- **Async SQLAlchemy** ORM with proper connection pooling

### **2. Modern Architecture Patterns**
- **Repository Pattern** for data access
- **Dependency Injection** throughout
- **Clean separation** of concerns
- **API Versioning** (`/api/v1/`)

### **3. Production-Ready Features**
- **Structured logging** with correlation IDs
- **Custom middleware** for error handling
- **Comprehensive error handling** with proper HTTP status codes
- **Request/Response validation** with Pydantic
- **Health checks** with database connectivity
- **Metrics & monitoring** endpoints

### **4. Developer Experience**
- **Auto-generated API docs** at `/docs`
- **Type hints** throughout
- **Comprehensive error messages**
- **Environment-based configuration**

## 🛠️ Configuration

### **Environment Variables**

```bash
# Database (auto-detected based on ENVIRONMENT)
ENVIRONMENT=development  # development, staging, production
DATABASE_URL=sqlite+aiosqlite:///path/to/db.db  # Optional override

# PostgreSQL (for production)
DB_USER=agentictrust
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agentictrust

# Server
HOST=0.0.0.0
PORT=8001
DEBUG=false

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # json or text
LOG_FILE=/path/to/logfile.log  # Optional

# Features
ENABLE_METRICS=true
ENABLE_TRACING=false
```

## 🚦 Running the Server

### **Development**
```bash
# From project root
python -m uvicorn agentictrust.backend.main:app --reload --port 8001

# Or using the convenience import
python -c "from agentictrust.backend import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8001, reload=True)"
```

### **Production**
```bash
# Set environment
export ENVIRONMENT=production
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_HOST=your_host

# Run with production settings
python -m uvicorn agentictrust.backend.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## 📡 API Endpoints

### **Health & System**
- `GET /` - Service information
- `GET /api/v1/health` - Health check with database connectivity
- `GET /api/v1/info` - System information and statistics
- `GET /api/v1/ready` - Kubernetes readiness probe
- `GET /api/v1/live` - Kubernetes liveness probe

### **MCP Server Management**
- `POST /api/v1/upstreams/` - Register new MCP server
- `GET /api/v1/upstreams/` - List all MCP servers (with pagination & filtering)
- `GET /api/v1/upstreams/{id}` - Get specific MCP server
- `DELETE /api/v1/upstreams/{id}` - Delete MCP server
- `GET /api/v1/upstreams/status/summary` - Status summary

### **Logging**
- `GET /api/v1/logs/` - Retrieve logs (with pagination & filtering)
- `POST /api/v1/logs/batch` - Ingest batch of logs
- `GET /api/v1/logs/stats` - Log statistics

### **Documentation**
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)
- `GET /api/v1/openapi.json` - OpenAPI schema

## 🌉 Agent-Aware MCP Bridge

The backend includes an Agent-Aware MCP Bridge server that provides authenticated access to MCP servers based on agent permissions.

### **Running the Bridge Server**

#### **Stdio Transport (for Claude Desktop)**
```bash
python -m agentictrust.backend.bridge --transport stdio
```

#### **SSE Transport (HTTP-based)**
```bash
python -m agentictrust.backend.bridge --transport sse --port 8100 --host 0.0.0.0
```

#### **StreamableHTTP Transport**
```bash
python -m agentictrust.backend.bridge --transport streamable-http --port 8100
```

### **Authentication Methods**

The bridge server supports two authentication methods:

1. **Header-Based Authentication (Recommended)**
   - `MCP_CLIENT_ID`: Your agent's client ID
   - `API_KEY`: Your agent's API key/client secret

2. **HTTP Basic Authentication**
   - Username: Your agent's client ID  
   - Password: Your agent's API key/client secret

### **Client Configuration Examples**

#### **Cursor/VS Code (with header support)**
```json
{
  "mcpServers": {
    "agent-bridge": {
      "url": "http://localhost:8100",
      "transport": "sse",
      "headers": {
        "MCP_CLIENT_ID": "your-client-id",
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

#### **Claude Desktop (using proxy for headers)**
Since Claude Desktop doesn't support custom headers, use the provided proxy:

```bash
# Run the proxy
python examples/mcp_header_proxy.py \
  --client-id your-client-id \
  --api-key your-api-key

# Configure Claude to use the proxy
{
  "mcpServers": {
    "agent-bridge": {
      "url": "http://localhost:8101",
      "transport": "sse"
    }
  }
}
```

#### **Testing the Connection**
```bash
# Test with the provided client
python examples/test_mcp_http_client.py

# Or test with curl
curl -X POST http://localhost:8100/messages \
  -H "MCP_CLIENT_ID: your-client-id" \
  -H "API_KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

### **Bridge Features**
- **Multi-tenant support**: Each agent sees only their permitted tools/resources
- **Usage tracking**: Tracks tool calls, resource reads, and prompt usage
- **Connection tracking**: Monitors active agent connections
- **Comprehensive logging**: All operations are logged for audit/debugging
- **Real-time filtering**: Dynamically filters capabilities based on agent permissions

## 🧪 Testing the API

### **Create an MCP Server**
```bash
curl -X POST http://localhost:8001/api/v1/upstreams/ \
  -H "Content-Type: application/json" \
  -d '{
    "command": "python",
    "args": ["-m", "mcp_server", "--port", "3000"],
    "name": "Test MCP Server",
    "description": "A test MCP server",
    "environment": "development"
  }'
```

### **List MCP Servers**
```bash
curl http://localhost:8001/api/v1/upstreams/
```

### **Health Check**
```bash
curl http://localhost:8001/api/v1/health
```

## 🗄️ Database Models

### **Upstream** (MCP Servers)
- `id` - Unique identifier
- `command` - Executable command
- `args` - Command arguments (JSON array)
- `name` - Human-readable name
- `description` - Server description
- `status` - Current status (registered, active, inactive, error)
- `environment` - Environment (development, staging, production)
- `config` - Additional configuration (JSON)
- `created_at` / `updated_at` - Timestamps

### **LogEntry** (System Logs)
- `id` - Auto-increment ID
- `timestamp` - ISO timestamp
- `event_type` - Type of event
- `data` - Event data (JSON)
- `correlation_id` - Request correlation ID
- `session_id` - Session grouping
- `source` - Source service/component
- `severity` - Log level (debug, info, warning, error, critical)

### **EventEntry** (Raw Events)
- `event_id` - Unique event ID
- `stream_id` - Stream identifier
- `timestamp` - Event timestamp
- `message_type` - Message type
- `method` - JSON-RPC method
- `message_data` - Complete message (JSON)
- `synced` - Processing status

### **ObservabilityEntry** (Processed Insights)
- `id` - Auto-increment ID
- `event_id` - Reference to source event
- `timestamp` - Processing timestamp
- `event_type` - Insight type
- `data` - Processed insights (JSON)
- `synced` - Sync status

## 🔧 Development

### **Adding New Endpoints**
1. Create endpoint in `api/v1/endpoints/`
2. Add router to `api/v1/router.py`
3. Create Pydantic schemas in `schemas/`
4. Add any new models to `data/models/`

### **Database Changes**
1. Modify models in `data/models/`
2. For production, use Alembic migrations
3. For development, drop and recreate tables

### **Custom Middleware**
Add to `core/middleware.py` and register in `main.py`

## 🎉 What's New

### **Compared to Previous Version**
- ✅ **Modern FastAPI structure** with proper separation of concerns
- ✅ **SQLAlchemy ORM** with async support
- ✅ **Multi-database support** (SQLite → PostgreSQL)
- ✅ **API versioning** for future compatibility
- ✅ **Structured logging** with correlation IDs
- ✅ **Comprehensive error handling** with custom exceptions
- ✅ **Request/Response validation** with Pydantic schemas
- ✅ **Health checks** and monitoring endpoints
- ✅ **Production-ready configuration** management
- ✅ **Auto-generated documentation**
- ✅ **Type hints** throughout the codebase

### **Backward Compatibility**
- Legacy SQLite functions available via `agentictrust.data.get_legacy_connection()`
- Existing database data preserved (with schema updates)
- Same core functionality with enhanced features

## 🚀 Next Steps

1. **Authentication & Authorization** - Add JWT/OAuth2 support
2. **Rate Limiting** - Add request rate limiting
3. **Caching** - Add Redis caching layer
4. **Metrics** - Add Prometheus metrics
5. **Testing** - Add comprehensive test suite
6. **Docker** - Add Docker configuration
7. **CI/CD** - Add GitHub Actions workflow

---

**The AgenticTrust backend is now production-ready with modern architecture patterns, comprehensive error handling, and excellent developer experience! 🎉** 