"""Endpoints for managing MCP servers"""

import uuid
from typing import Optional, List, Tuple
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from agentictrust.backend.api.dependencies import DatabaseSession
from agentictrust.backend.schemas.mcp import (
    MCPBase,
    MCPUpdate,
    MCPResponse,
    MCPListResponse,
    MCPServersConfig,
    MCPServerConfig,
    ServerType,
)
from agentictrust.backend.schemas.responses import DeleteResponse, SuccessResponse
from agentictrust.backend.data.models.mcp import MCP
from agentictrust.backend.core.exceptions import DatabaseError, NotFoundError
from agentictrust.backend.core.mcp import Engine
from agentictrust.backend.schemas.mcp import MCPTestResult
from pydantic import Field
from agentictrust.backend.schemas.mcp import MCPDetailedResponse
from agentictrust.backend.data.models.tool import Tool
from agentictrust.backend.data.models.resource import Resource
from agentictrust.backend.data.models.prompt import Prompt

router = APIRouter()


async def check_mcp_duplicates(db: AsyncSession, config: MCPBase, exclude_id: Optional[str] = None) -> List[str]:
    """
    Check for duplicate MCP configurations and return list of conflict descriptions.
    
    Args:
        db: Database session
        config: MCP configuration to check
        exclude_id: Optional MCP ID to exclude from duplicate check (for updates)
        
    Returns:
        List of conflict descriptions. Empty list if no duplicates found.
    """
    conflicts = []
    
    # Build base query
    query = select(MCP)
    if exclude_id:
        query = query.where(MCP.id != exclude_id)
    
    # Check for name duplicates within the same environment
    if config.name and config.name.strip():
        name_query = query.where(
            and_(
                MCP.name == config.name.strip(),
                MCP.environment == config.environment
            )
        )
        existing_name = (await db.execute(name_query)).scalar_one_or_none()
        if existing_name:
            conflicts.append(f"MCP with name '{config.name}' already exists in environment '{config.environment}'")
    
    # Check for configuration duplicates
    if config.server_type == ServerType.COMMAND and config.command:
        # For command servers, check command + args combination
        cmd_query = query.where(
            and_(
                MCP.server_type == "command",
                MCP.command == config.command.strip(),
                MCP.args == config.args
            )
        )
        existing_cmd = (await db.execute(cmd_query)).scalar_one_or_none()
        if existing_cmd:
            args_str = " ".join(config.args) if config.args else "(no args)"
            conflicts.append(f"Command server with command '{config.command}' and args '{args_str}' already exists")
    
    elif config.server_type in (ServerType.URL, ServerType.SSE) and config.url:
        # For URL/SSE servers, check URL
        url_query = query.where(
            and_(
                MCP.server_type.in_(["url", "sse"]),
                MCP.url == config.url.strip()
            )
        )
        existing_url = (await db.execute(url_query)).scalar_one_or_none()
        if existing_url:
            conflicts.append(f"Server with URL '{config.url}' already exists")
    
    return conflicts


async def check_bulk_duplicates(db: AsyncSession, configs: List[Tuple[str, MCPBase]]) -> List[str]:
    """
    Check for duplicates in bulk registration including both existing and within the batch.
    
    Args:
        db: Database session
        configs: List of (name, config) tuples to check
        
    Returns:
        List of conflict descriptions. Empty list if no duplicates found.
    """
    conflicts = []
    
    # Check for duplicates within the batch itself
    names_seen = set()
    configs_seen = set()
    
    for name, config in configs:
        # Check name duplicates within batch
        if config.name:
            name_key = (config.name.strip(), config.environment)
            if name_key in names_seen:
                conflicts.append(f"Duplicate name '{config.name}' found within the batch for environment '{config.environment}'")
            names_seen.add(name_key)
        
        # Check config duplicates within batch
        if config.server_type == ServerType.COMMAND and config.command:
            config_key = ("command", config.command.strip(), tuple(config.args or []))
        elif config.server_type in (ServerType.URL, ServerType.SSE) and config.url:
            config_key = ("url", config.url.strip())
        else:
            continue
            
        if config_key in configs_seen:
            conflicts.append(f"Duplicate configuration found within the batch: {config_key}")
        configs_seen.add(config_key)
    
    # Check against existing database entries
    for name, config in configs:
        existing_conflicts = await check_mcp_duplicates(db, config)
        conflicts.extend(existing_conflicts)
    
    return conflicts


@router.post("/", response_model=MCPResponse, summary="Register a new MCP server")
async def register_mcp_server(config: MCPBase, db: AsyncSession = DatabaseSession):
    """Register a new MCP server with duplicate detection"""
    
    # Check for duplicates
    conflicts = await Engine.check_duplicates(db, config)
    if conflicts:
        raise HTTPException(
            status_code=409, 
            detail={
                "message": "MCP registration conflicts detected",
                "conflicts": conflicts
            }
        )
    
    try:
        mcp = await Engine.register(db, config)
        return MCPResponse.from_orm(mcp)
    except Exception as e:
        await db.rollback()
        raise DatabaseError(str(e))


@router.post("/bulk", response_model=SuccessResponse, summary="Bulk register MCP servers")
async def bulk_register(config: MCPServersConfig, db: AsyncSession = DatabaseSession):
    """Bulk register MCP servers with comprehensive duplicate detection"""
    
    # Convert to list of MCPBase configs for validation
    configs_to_validate = []
    for name, entry in config.mcpServers.items():
        server_type = Engine.determine_server_type_from_json(entry.dict())
        
        # Create MCPBase instance for validation
        mcp_config = MCPBase(
            name=name,
            server_type=server_type,
            command=entry.command,
            args=entry.args or [],
            url=entry.url,
            env=entry.env or {},
            environment="development"  # Default environment for bulk import
        )
        configs_to_validate.append((name, mcp_config))
    
    # Check for duplicates
    conflicts = await Engine.bulk_check_duplicates(db, configs_to_validate)
    if conflicts:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Bulk registration conflicts detected",
                "conflicts": conflicts,
                "total_conflicts": len(conflicts)
            }
        )
    
    # If no conflicts, proceed with registration
    try:
        created = 0
        for name, entry in config.mcpServers.items():
            server_type = Engine.determine_server_type_from_json(entry.dict())
            if server_type == ServerType.COMMAND:
                mcp = MCP(
                    id=str(uuid.uuid4()),
                    server_type="command",
                    command=entry.command,
                    args=entry.args or [],
                    env=entry.env or {},
                    name=name,
                    status="registered",
                )
            else:
                mcp = MCP(
                    id=str(uuid.uuid4()),
                    server_type=server_type.value,
                    url=entry.url,
                    env=entry.env or {},
                    name=name,
                    status="registered",
                )
            db.add(mcp)
            created += 1
        await db.commit()
        return SuccessResponse(message=f"Successfully created {created} MCP servers")
    except Exception as e:
        await db.rollback()
        raise DatabaseError(str(e))


@router.get("/", response_model=MCPListResponse, summary="List MCP servers")
async def list_mcp(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    server_type: Optional[ServerType] = None,
    environment: Optional[str] = None,
    db: AsyncSession = DatabaseSession,
):
    rows, total = await Engine.list(
        db,
        skip=skip,
        limit=limit,
        status=status,
        server_type=server_type,
        environment=environment,
    )
    return MCPListResponse(
        items=[MCPResponse.from_orm(r) for r in rows],
        total=total,
        page=(skip // limit) + 1,
        size=limit,
    )


@router.get("/{mcp_id}", response_model=MCPResponse, summary="Get MCP server by id")
async def get_mcp(mcp_id: str, db: AsyncSession = DatabaseSession):
    mcp = await Engine.get(db, mcp_id)
    if not mcp:
        raise NotFoundError("MCP", mcp_id)

    # Attach counts for tools/resources/prompts
    tools_total = (
        await db.execute(select(func.count()).select_from(Tool).where(Tool.mcp_id == mcp_id))
    ).scalar()
    resources_total = (
        await db.execute(select(func.count()).select_from(Resource).where(Resource.mcp_id == mcp_id))
    ).scalar()
    prompts_total = (
        await db.execute(select(func.count()).select_from(Prompt).where(Prompt.mcp_id == mcp_id))
    ).scalar()

    # Names
    tools_names = (
        await db.execute(select(Tool.name).where(Tool.mcp_id == mcp_id))
    ).scalars().all()
    resources_names = (
        await db.execute(select(Resource.name).where(Resource.mcp_id == mcp_id))
    ).scalars().all()
    prompts_names = (
        await db.execute(select(Prompt.name).where(Prompt.mcp_id == mcp_id))
    ).scalars().all()

    setattr(mcp, "tools_count", tools_total or 0)
    setattr(mcp, "resources_count", resources_total or 0)
    setattr(mcp, "prompts_count", prompts_total or 0)

    setattr(mcp, "tool_names", tools_names or [])
    setattr(mcp, "resource_names", resources_names or [])
    setattr(mcp, "prompt_names", prompts_names or [])

    return MCPResponse.from_orm(mcp)


@router.put("/{mcp_id}", response_model=MCPResponse, summary="Update MCP server")
async def update_mcp(mcp_id: str, updates: MCPUpdate, db: AsyncSession = DatabaseSession):
    """Update MCP server with duplicate detection for changes"""
    
    mcp = await Engine.get(db, mcp_id)
    if not mcp:
        raise NotFoundError("MCP", mcp_id)
    
    # Create a temporary config with updated values for duplicate checking
    updated_config = MCPBase(
        name=updates.name if updates.name is not None else mcp.name,
        server_type=updates.server_type if updates.server_type is not None else ServerType(mcp.server_type),
        command=updates.command if updates.command is not None else mcp.command,
        args=updates.args if updates.args is not None else mcp.args_list,
        url=updates.url if updates.url is not None else mcp.url,
        env=updates.env if updates.env is not None else mcp.env_dict,
        environment=updates.environment if updates.environment is not None else mcp.environment,
    )
    
    # Check for duplicates (excluding current MCP)
    conflicts = await Engine.check_duplicates(db, updated_config, exclude_id=mcp_id)
    if conflicts:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "MCP update conflicts detected",
                "conflicts": conflicts
            }
        )
    
    mcp = await Engine.update(db, mcp, updates)
    return MCPResponse.from_orm(mcp)


@router.delete("/{mcp_id}", response_model=DeleteResponse, summary="Delete MCP server")
async def delete_mcp(mcp_id: str, db: AsyncSession = DatabaseSession):
    mcp = await Engine.get(db, mcp_id)
    if not mcp:
        raise NotFoundError("MCP", mcp_id)
    await Engine.delete(db, mcp_id)
    return DeleteResponse(id=mcp_id, message="deleted")


@router.get("/status/summary", summary="Summary stats")
async def status_summary(db: AsyncSession = DatabaseSession):
    return await Engine.status_summary(db)


@router.post("/validate", summary="Validate MCP configuration without saving")
async def validate_mcp_config(config: MCPBase, db: AsyncSession = DatabaseSession):
    """
    Validate MCP configuration and check for duplicates without actually registering.
    Useful for frontend validation before submission.
    """
    conflicts = await Engine.check_duplicates(db, config)
    
    return await Engine.validate(db, config)


# ---------------------------------------------------------------------------
# Pre-registration connectivity test
# ---------------------------------------------------------------------------


@router.post("/test", response_model=MCPTestResult, summary="Test MCP server connectivity and introspect capabilities")
async def test_mcp_server(config: MCPBase):
    """Connect to the provided MCP configuration, initialise the protocol and
    fetch the list of tools, resources and prompts. Nothing is persisted – this
    is intended for pre-registration validation in the frontend workflow."""

    try:
        tools, resources, prompts = await Engine.test(config)
        return MCPTestResult(tools=tools, resources=resources, prompts=prompts)
    except Exception as e:
        # Engine.test raises MCPTransportError internally
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Detailed view endpoint (includes tools/resources/prompts)
# ---------------------------------------------------------------------------


@router.get("/{mcp_id}/view", response_model=MCPDetailedResponse, summary="Get MCP with capabilities")
async def get_mcp_with_capabilities(mcp_id: str, db: AsyncSession = DatabaseSession):
    mcp = await Engine.get(db, mcp_id)
    if not mcp:
        raise NotFoundError("MCP", mcp_id)

    detailed = await Engine.get_with_capabilities(db, mcp_id)
    return detailed


# ---------------------------------------------------------------------------
# Fleet health report
# ---------------------------------------------------------------------------

@router.get("/health/report", summary="Fleet health report")
async def fleet_health_report(db: AsyncSession = DatabaseSession):
    """Return overall MCP fleet health and per-MCP issues."""
    return await Engine.health_report(db) 