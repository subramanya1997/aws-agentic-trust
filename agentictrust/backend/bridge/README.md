# Agent-Aware MCP Bridge Server

The Agent-Aware MCP Bridge Server is a multi-tenant MCP server that dynamically filters tools, resources, and prompts based on authenticated agent credentials. Each agent sees only their permitted subset of capabilities from the registered upstream MCP servers.

## Features

- **Multi-tenant**: Each agent gets their own filtered view of capabilities
- **Authentication**: HTTP Basic auth using agent client_id/client_secret
- **Multiple Transports**: Supports stdio, SSE, and StreamableHTTP
- **Dynamic Filtering**: Real-time capability filtering based on agent permissions
- **Upstream Aggregation**: Connects to all registered MCP servers in the database

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   Bridge Server │    │ Upstream MCPs   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Agent Creds │ │───▶│ │ Auth Layer  │ │    │ │   Server A  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │        │        │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ MCP Calls   │ │◀───│ │ Filter Layer│ │◀───│ │   Server B  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Usage

### Standalone Server

Run the bridge server as a standalone service:

```bash
# SSE transport (default)
python -m agentictrust.backend.bridge --transport sse --port 8100

# stdio transport
python -m agentictrust.backend.bridge --transport stdio

# StreamableHTTP transport
python -m agentictrust.backend.bridge --transport streamable-http --port 8200
```

### Mounted in FastAPI

The bridge is automatically mounted in the main FastAPI application under `/api/v1/bridge/`:

- **SSE endpoint**: `http://localhost:8001/api/v1/bridge/sse`
- **HTTP endpoint**: `http://localhost:8001/api/v1/bridge/http`
- **Info endpoint**: `http://localhost:8001/api/v1/bridge/info`

## Authentication

All requests require HTTP Basic authentication:

- **Username**: Agent `client_id`
- **Password**: Agent `client_secret`

Example with curl:
```bash
curl -u "agent_client_id:agent_secret" \
  http://localhost:8100/sse
```

## MCP Client Configuration

### Claude Desktop (SSE)

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "agent-bridge": {
      "command": "curl",
      "args": [
        "-u", "your_agent_client_id:your_agent_secret",
        "-H", "Accept: text/event-stream",
        "http://localhost:8100/sse"
      ]
    }
  }
}
```

### Python MCP Client (SSE)

```python
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

headers = {
    "Authorization": "Basic " + base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()
}

async with sse_client("http://localhost:8100/sse", headers=headers) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools.tools]}")
```

### Python MCP Client (stdio)

```python
import subprocess
import base64
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

# Set auth via environment
auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
env = {"BRIDGE_AUTH": f"Basic {auth_header}"}

async with stdio_client(
    command="python",
    args=["-m", "agentictrust.backend.bridge", "--transport", "stdio"],
    env=env
) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # Use the session...
```

## Agent Permissions

The bridge filters capabilities based on the authenticated agent's permissions:

- **Tools**: Only tools with IDs in `agent.allowed_tool_ids` are visible
- **Resources**: Only resources with IDs in `agent.allowed_resource_ids` are accessible  
- **Prompts**: Only prompts with IDs in `agent.allowed_prompt_ids` are available

## Configuration

Environment variables:

- `BRIDGE_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DATABASE_URL`: Database connection string
- `AGENTICTRUST_SERVER_URL`: Backend server URL

## Development

### Running Tests

```bash
# Run bridge server tests
pytest agentictrust/backend/bridge/tests/

# Test with a real agent
python -m agentictrust.backend.bridge --transport sse --port 8100 &
curl -u "test_client_id:test_secret" http://localhost:8100/sse
```

### Adding New Transports

To add a new transport:

1. Extend `AgentAwareMCPBridge` with transport-specific methods
2. Update `main.py` to handle the new transport
3. Add authentication middleware support
4. Update documentation

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Verify agent credentials are correct
2. **No Tools/Resources**: Check agent permissions in database
3. **Upstream Connection Failed**: Verify MCP servers are running and accessible
4. **Port Already in Use**: Change port with `--port` flag

### Debugging

Enable debug logging:
```bash
python -m agentictrust.backend.bridge --log-level DEBUG
```

Check agent permissions:
```bash
curl -u "client_id:secret" http://localhost:8001/api/v1/agents/me
```

## Security Considerations

- Agent credentials are transmitted via HTTP Basic auth (use HTTPS in production)
- Each agent can only access their permitted capabilities
- Upstream MCP connections are isolated per request
- No capability data is cached between requests

## Performance

- Upstream connections are established during server startup
- Capability filtering happens in-memory
- Database queries are optimized with proper indexing
- Connection pooling is used for database access 