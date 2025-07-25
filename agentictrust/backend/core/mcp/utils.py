from uuid import uuid4
from typing import Dict

from agentictrust.backend.data.models.mcp import MCP
from agentictrust.backend.schemas.mcp import MCPBase, ServerType


def validate_config(config: MCPBase) -> None:
    # Pydantic validation already executed on instantiation – placeholder.
    return


def to_db_model(config: MCPBase) -> MCP:
    """Convert an MCPBase schema into an MCP SQLAlchemy model instance."""
    return MCP(
        id=str(uuid4()),
        server_type=config.server_type.value,
        command=config.command,
        args=config.args,
        url=config.url,
        env=config.env,
        name=config.name,
        description=config.description,
        environment=config.environment,
        config=config.config,
        status="registered",
    )


def determine_server_type_from_json(entry: Dict) -> ServerType:
    """Infer server_type from a raw JSON dict entry of the form used in bulk import."""
    if "command" in entry:
        return ServerType.COMMAND
    if "url" in entry:
        lower_url = entry["url"].lower()
        if "sse" in lower_url or "stream" in lower_url:
            return ServerType.SSE
        return ServerType.URL
    # default fallback
    return ServerType.COMMAND 