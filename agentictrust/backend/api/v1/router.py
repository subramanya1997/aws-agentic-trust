"""Main API router for version 1"""

from fastapi import APIRouter

# noqa: E501
# fmt: off
from agentictrust.backend.api.v1.endpoints import health, mcp, logs, agents, capabilities, usage_stats
# fmt: on

# Create the main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
# New agent credential endpoints
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
# Capabilities listing
api_router.include_router(capabilities.router, prefix="/capabilities", tags=["capabilities"])
# Usage statistics and connection tracking
api_router.include_router(usage_stats.router, prefix="/usage", tags=["usage-stats"]) 