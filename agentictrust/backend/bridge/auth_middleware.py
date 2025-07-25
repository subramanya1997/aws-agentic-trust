from __future__ import annotations

"""Authentication middleware for the Agent-Aware MCP Bridge."""

import base64
import logging
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

from agentictrust.backend.config.database import AsyncSessionLocal
from agentictrust.backend.core.agent import Engine as AgentEngine
from agentictrust.backend.data.models.agent import Agent

logger = logging.getLogger(__name__)


class BridgeAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate agents and set context for the bridge server."""

    def __init__(self, app: ASGIApp, bridge_server) -> None:
        super().__init__(app)
        self.bridge_server = bridge_server

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Authenticate the request and set agent context."""
        
        client_id = None
        client_secret = None
        
        # First, try to get credentials from custom headers
        mcp_client_id = request.headers.get("MCP_CLIENT_ID")
        api_key = request.headers.get("API_KEY")
        
        if mcp_client_id and api_key:
            # Use custom headers
            client_id = mcp_client_id
            client_secret = api_key
            logger.debug(f"Using header-based authentication for client_id: {client_id}")
        else:
            # Fall back to HTTP Basic auth
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Basic "):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Missing authentication. Provide either MCP_CLIENT_ID/API_KEY headers or Basic Authorization"}
                )

            try:
                # Decode Basic auth
                encoded_credentials = auth_header[6:]  # Remove "Basic "
                decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
                client_id, client_secret = decoded_credentials.split(":", 1)
                logger.debug(f"Using Basic auth for client_id: {client_id}")
            except (ValueError, UnicodeDecodeError):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid Authorization header format"}
                )

        # Authenticate agent
        try:
            async with AsyncSessionLocal() as db:
                agent = await AgentEngine.authenticate(db, client_id, client_secret)
                
            # Set agent context in bridge server
            self.bridge_server.set_current_agent(agent)
            
            # Store agent in request state for potential use
            request.state.agent = agent
            
            logger.info(f"Authenticated agent: {agent.name} ({agent.client_id})")
            
        except Exception as e:
            logger.warning(f"Authentication failed for client_id {client_id}: {e}")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid credentials"}
            )

        # Continue with the request
        response = await call_next(request)
        return response 