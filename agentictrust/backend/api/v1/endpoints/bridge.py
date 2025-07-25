"""Bridge endpoints for mounting the MCP bridge server in FastAPI.

This provides REST endpoints that delegate to the AgentAwareMCPBridge server,
allowing the bridge to be accessed via both MCP protocols and REST API.
"""

from fastapi import APIRouter, Request, Response
from starlette.applications import Starlette

from agentictrust.backend.bridge.server import AgentAwareMCPBridge
from agentictrust.backend.bridge.auth_middleware import BridgeAuthMiddleware

router = APIRouter(prefix="/bridge", tags=["bridge"])

# Create a single bridge instance for the FastAPI mount
_bridge_instance = AgentAwareMCPBridge()


@router.get("/info", summary="Bridge server information")
async def bridge_info():
    """Return information about the bridge server."""
    return {
        "name": _bridge_instance.name,
        "instructions": _bridge_instance.instructions,
        "transport": "mounted",
        "description": "Agent-aware MCP bridge server mounted in FastAPI",
    }


# Mount the bridge SSE app under /sse
@router.mount("/sse", _bridge_instance.sse_app())

# Mount the bridge StreamableHTTP app under /http  
@router.mount("/http", _bridge_instance.streamable_http_app())


# Add authentication middleware to the bridge apps
def setup_bridge_auth():
    """Setup authentication middleware for mounted bridge apps."""
    # Get the SSE app and add auth middleware
    sse_app = _bridge_instance.sse_app()
    sse_app.add_middleware(BridgeAuthMiddleware, bridge_server=_bridge_instance)
    
    # Get the HTTP app and add auth middleware
    http_app = _bridge_instance.streamable_http_app()
    http_app.add_middleware(BridgeAuthMiddleware, bridge_server=_bridge_instance)


# Setup auth when module is imported
setup_bridge_auth() 