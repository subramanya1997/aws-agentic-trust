from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from agentictrust.backend.api.dependencies import DatabaseSession
from agentictrust.backend.schemas.agent import (
    AgentCreate,
    AgentRegistrationResponse,
    AgentResponse,
    AgentCredentials,
    AgentListResponse,
    AgentUpdate,
)
from agentictrust.backend.schemas.responses import DeleteResponse
from agentictrust.backend.data.models.agent import Agent
from agentictrust.backend.core.exceptions import DatabaseError, NotFoundError
from agentictrust.backend.core.agent import Engine as AgentEngine

router = APIRouter()

security = HTTPBasic()


# ---------------------------------------------------------------------------
# Authentication dependency for agent-scoped endpoints
# ---------------------------------------------------------------------------

async def _authenticate_agent(
    credentials: HTTPBasicCredentials = Depends(security),
    db: AsyncSession = DatabaseSession,
) -> Agent:
    """Verify HTTP Basic credentials and return the corresponding Agent row."""
    client_id = credentials.username
    provided_secret = credentials.password

    try:
        agent = await AgentEngine.authenticate(db, client_id, provided_secret)
        return agent
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")


AuthenticatedAgent = Depends(_authenticate_agent)


# ---------------------------------------------------------------------------
# Registration endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=AgentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent and obtain credentials",
)
async def register_agent(payload: AgentCreate, db: AsyncSession = DatabaseSession):
    """Register a new agent identity via the Agent Engine."""

    try:
        agent, client_secret = await AgentEngine.register(db, payload)
    except DatabaseError as exc:
        # Re-raise as HTTP 400/409 depending on context – here we treat as 400.
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Build response with empty capability objects for new agent
    agent_data = {
        **agent.to_dict(),
        "tool_ids": agent.allowed_tool_ids or [],
        "resource_ids": agent.allowed_resource_ids or [],
        "prompt_ids": agent.allowed_prompt_ids or [],
        "tools": [],
        "resources": [],
        "prompts": [],
    }
    
    return AgentRegistrationResponse(
        agent=AgentResponse(**agent_data),
        credentials=AgentCredentials(client_id=agent.client_id, client_secret=client_secret),
    )


# ---------------------------------------------------------------------------
# List endpoint (pagination)
# ---------------------------------------------------------------------------

@router.get("/", summary="List registered agents", response_model=AgentListResponse)
async def list_agents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = DatabaseSession,
):
    return await AgentEngine.list_detailed(db, skip=skip, limit=limit)


# ---------------------------------------------------------------------------
# Capability-scoped query endpoints (example: list tools)
# ---------------------------------------------------------------------------

@router.get("/me", response_model=AgentResponse, summary="Get current agent profile")
async def get_current_agent(agent: Agent = AuthenticatedAgent):
    return AgentEngine.agent_basic_response(agent)


@router.get("/tools", summary="List tools accessible to the authenticated agent")
async def list_agent_tools(agent: Agent = AuthenticatedAgent, db: AsyncSession = DatabaseSession):
    return await AgentEngine.list_tools(db, agent)


@router.get("/resources", summary="List resources accessible to the authenticated agent")
async def list_agent_resources(agent: Agent = AuthenticatedAgent, db: AsyncSession = DatabaseSession):
    return await AgentEngine.list_resources(db, agent)


@router.get("/prompts", summary="List prompts accessible to the authenticated agent")
async def list_agent_prompts(agent: Agent = AuthenticatedAgent, db: AsyncSession = DatabaseSession):
    return await AgentEngine.list_prompts(db, agent)


# ---------------------------------------------------------------------------
# Delete endpoint
# ---------------------------------------------------------------------------

@router.delete("/{agent_id}", response_model=DeleteResponse, summary="Delete agent")
async def delete_agent(agent_id: str, db: AsyncSession = DatabaseSession):
    """Delete an agent by ID."""
    agent = await AgentEngine.get(db, agent_id)
    if not agent:
        raise NotFoundError("Agent", agent_id)
    
    await AgentEngine.delete(db, agent_id)
    return DeleteResponse(id=agent_id, message="Agent deleted successfully")


# ---------------------------------------------------------------------------
# Update endpoint
# ---------------------------------------------------------------------------

@router.put("/{agent_id}", response_model=AgentResponse, summary="Update agent")
async def update_agent(agent_id: str, updates: AgentUpdate, db: AsyncSession = DatabaseSession):
    """Update an existing agent profile (metadata and capability lists)."""

    agent = await AgentEngine.get(db, agent_id)
    if not agent:
        raise NotFoundError("Agent", agent_id)

    updated = await AgentEngine.update(db, agent, updates)

    # Return basic response (no credentials)
    return AgentEngine.agent_basic_response(updated)


# ---------------------------------------------------------------------------
# Status summary endpoint
# ---------------------------------------------------------------------------

@router.get("/status/summary", summary="Get agent status summary")
async def get_agent_status_summary(db: AsyncSession = DatabaseSession):
    """Get summary statistics for agents (delegated to core Engine)."""
    return await AgentEngine.status_summary(db) 