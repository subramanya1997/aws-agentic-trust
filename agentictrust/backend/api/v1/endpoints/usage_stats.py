"""API endpoints for MCP usage statistics and connection tracking"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from agentictrust.backend.config.database import get_db
from agentictrust.backend.data.models.mcp import MCP
from agentictrust.backend.data.models.agent import Agent
from agentictrust.backend.data.models.tool import Tool
from agentictrust.backend.data.models.resource import Resource
from agentictrust.backend.data.models.prompt import Prompt
from agentictrust.backend.data.models.usage_tracking import (
    AgentMCPUsage,
    AgentToolUsage,
    AgentResourceUsage,
    AgentPromptUsage,
)

router = APIRouter()


@router.get("/mcps/connections")
async def get_mcp_connections(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get MCP server connection statistics."""
    
    # Get MCPs with connection info
    mcps = (await db.execute(
        select(MCP).order_by(MCP.connected_instances.desc(), MCP.name)
    )).scalars().all()
    
    result = []
    for mcp in mcps:
        # Get connected agents
        connected_agents = (await db.execute(
            select(AgentMCPUsage, Agent)
            .join(Agent, AgentMCPUsage.agent_id == Agent.id)
            .where(
                AgentMCPUsage.mcp_id == mcp.id,
                AgentMCPUsage.is_connected == "true"
            )
        )).all()
        
        agent_info = [
            {
                "agent_id": usage.agent_id,
                "agent_name": agent.name,
                "connected_at": usage.connected_at.isoformat() if usage.connected_at else None,
                "total_tool_calls": usage.total_tool_calls,
                "total_resource_reads": usage.total_resource_reads,
                "total_prompt_gets": usage.total_prompt_gets,
                "last_activity_at": usage.last_activity_at.isoformat() if usage.last_activity_at else None,
            }
            for usage, agent in connected_agents
        ]
        
        result.append({
            "mcp_id": mcp.id,
            "name": mcp.name,
            "server_type": mcp.server_type,
            "status": mcp.status,
            "connected_instances": mcp.connected_instances,
            "total_connections": mcp.total_connections,
            "last_connected_at": mcp.last_connected_at.isoformat() if mcp.last_connected_at else None,
            "last_disconnected_at": mcp.last_disconnected_at.isoformat() if mcp.last_disconnected_at else None,
            "connected_agents": agent_info,
        })
    
    return result


@router.get("/tools/usage")
async def get_tool_usage(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get tool usage statistics."""
    
    # Get tools with usage stats
    tools_usage = (await db.execute(
        select(
            Tool,
            MCP,
            func.count(AgentToolUsage.id).label("agent_count"),
            func.sum(AgentToolUsage.total_calls).label("total_calls"),
            func.max(AgentToolUsage.last_called_at).label("last_used_at")
        )
        .join(MCP, Tool.mcp_id == MCP.id)
        .outerjoin(AgentToolUsage, Tool.id == AgentToolUsage.tool_id)
        .group_by(Tool.id, MCP.id)
        .order_by(func.sum(AgentToolUsage.total_calls).desc().nullslast())
    )).all()
    
    result = []
    for tool, mcp, agent_count, total_calls, last_used_at in tools_usage:
        # Get agent details for this tool
        agent_usage = (await db.execute(
            select(AgentToolUsage, Agent)
            .join(Agent, AgentToolUsage.agent_id == Agent.id)
            .where(AgentToolUsage.tool_id == tool.id)
            .order_by(AgentToolUsage.total_calls.desc())
        )).all()
        
        agent_info = [
            {
                "agent_id": usage.agent_id,
                "agent_name": agent.name,
                "total_calls": usage.total_calls,
                "first_called_at": usage.first_called_at.isoformat() if usage.first_called_at else None,
                "last_called_at": usage.last_called_at.isoformat() if usage.last_called_at else None,
            }
            for usage, agent in agent_usage
        ]
        
        result.append({
            "tool_id": tool.id,
            "tool_name": tool.name,
            "tool_description": tool.description,
            "mcp_name": mcp.name,
            "mcp_status": mcp.status,
            "agent_count": agent_count or 0,
            "total_calls": total_calls or 0,
            "last_used_at": last_used_at.isoformat() if last_used_at else None,
            "using_agents": agent_info,
        })
    
    return result


@router.get("/resources/usage")
async def get_resource_usage(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get resource usage statistics."""
    
    # Get resources with usage stats
    resources_usage = (await db.execute(
        select(
            Resource,
            MCP,
            func.count(AgentResourceUsage.id).label("agent_count"),
            func.sum(AgentResourceUsage.total_reads).label("total_reads"),
            func.max(AgentResourceUsage.last_read_at).label("last_used_at")
        )
        .join(MCP, Resource.mcp_id == MCP.id)
        .outerjoin(AgentResourceUsage, Resource.id == AgentResourceUsage.resource_id)
        .group_by(Resource.id, MCP.id)
        .order_by(func.sum(AgentResourceUsage.total_reads).desc().nullslast())
    )).all()
    
    result = []
    for resource, mcp, agent_count, total_reads, last_used_at in resources_usage:
        # Get agent details for this resource
        agent_usage = (await db.execute(
            select(AgentResourceUsage, Agent)
            .join(Agent, AgentResourceUsage.agent_id == Agent.id)
            .where(AgentResourceUsage.resource_id == resource.id)
            .order_by(AgentResourceUsage.total_reads.desc())
        )).all()
        
        agent_info = [
            {
                "agent_id": usage.agent_id,
                "agent_name": agent.name,
                "total_reads": usage.total_reads,
                "first_read_at": usage.first_read_at.isoformat() if usage.first_read_at else None,
                "last_read_at": usage.last_read_at.isoformat() if usage.last_read_at else None,
            }
            for usage, agent in agent_usage
        ]
        
        result.append({
            "resource_id": resource.id,
            "resource_name": resource.name,
            "resource_uri": resource.uri,
            "resource_description": resource.description,
            "mcp_name": mcp.name,
            "mcp_status": mcp.status,
            "agent_count": agent_count or 0,
            "total_reads": total_reads or 0,
            "last_used_at": last_used_at.isoformat() if last_used_at else None,
            "using_agents": agent_info,
        })
    
    return result


@router.get("/prompts/usage")
async def get_prompt_usage(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get prompt usage statistics."""
    
    # Get prompts with usage stats
    prompts_usage = (await db.execute(
        select(
            Prompt,
            MCP,
            func.count(AgentPromptUsage.id).label("agent_count"),
            func.sum(AgentPromptUsage.total_gets).label("total_gets"),
            func.max(AgentPromptUsage.last_got_at).label("last_used_at")
        )
        .join(MCP, Prompt.mcp_id == MCP.id)
        .outerjoin(AgentPromptUsage, Prompt.id == AgentPromptUsage.prompt_id)
        .group_by(Prompt.id, MCP.id)
        .order_by(func.sum(AgentPromptUsage.total_gets).desc().nullslast())
    )).all()
    
    result = []
    for prompt, mcp, agent_count, total_gets, last_used_at in prompts_usage:
        # Get agent details for this prompt
        agent_usage = (await db.execute(
            select(AgentPromptUsage, Agent)
            .join(Agent, AgentPromptUsage.agent_id == Agent.id)
            .where(AgentPromptUsage.prompt_id == prompt.id)
            .order_by(AgentPromptUsage.total_gets.desc())
        )).all()
        
        agent_info = [
            {
                "agent_id": usage.agent_id,
                "agent_name": agent.name,
                "total_gets": usage.total_gets,
                "first_got_at": usage.first_got_at.isoformat() if usage.first_got_at else None,
                "last_got_at": usage.last_got_at.isoformat() if usage.last_got_at else None,
            }
            for usage, agent in agent_usage
        ]
        
        result.append({
            "prompt_id": prompt.id,
            "prompt_name": prompt.name,
            "prompt_description": prompt.description,
            "mcp_name": mcp.name,
            "mcp_status": mcp.status,
            "agent_count": agent_count or 0,
            "total_gets": total_gets or 0,
            "last_used_at": last_used_at.isoformat() if last_used_at else None,
            "using_agents": agent_info,
        })
    
    return result


@router.get("/agents/{agent_id}/usage")
async def get_agent_usage(
    agent_id: str, 
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get usage statistics for a specific agent."""
    
    # Verify agent exists
    agent = (await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )).scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get MCP usage
    mcp_usage = (await db.execute(
        select(AgentMCPUsage, MCP)
        .join(MCP, AgentMCPUsage.mcp_id == MCP.id)
        .where(AgentMCPUsage.agent_id == agent_id)
        .order_by(AgentMCPUsage.last_activity_at.desc().nullslast())
    )).all()
    
    # Get tool usage
    tool_usage = (await db.execute(
        select(AgentToolUsage, Tool, MCP)
        .join(Tool, AgentToolUsage.tool_id == Tool.id)
        .join(MCP, Tool.mcp_id == MCP.id)
        .where(AgentToolUsage.agent_id == agent_id)
        .order_by(AgentToolUsage.total_calls.desc())
    )).all()
    
    # Get resource usage
    resource_usage = (await db.execute(
        select(AgentResourceUsage, Resource, MCP)
        .join(Resource, AgentResourceUsage.resource_id == Resource.id)
        .join(MCP, Resource.mcp_id == MCP.id)
        .where(AgentResourceUsage.agent_id == agent_id)
        .order_by(AgentResourceUsage.total_reads.desc())
    )).all()
    
    # Get prompt usage
    prompt_usage = (await db.execute(
        select(AgentPromptUsage, Prompt, MCP)
        .join(Prompt, AgentPromptUsage.prompt_id == Prompt.id)
        .join(MCP, Prompt.mcp_id == MCP.id)
        .where(AgentPromptUsage.agent_id == agent_id)
        .order_by(AgentPromptUsage.total_gets.desc())
    )).all()
    
    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "mcp_connections": [
            {
                "mcp_id": mcp.id,
                "mcp_name": mcp.name,
                "is_connected": usage.is_connected == "true",
                "connected_at": usage.connected_at.isoformat() if usage.connected_at else None,
                "disconnected_at": usage.disconnected_at.isoformat() if usage.disconnected_at else None,
                "total_tool_calls": usage.total_tool_calls,
                "total_resource_reads": usage.total_resource_reads,
                "total_prompt_gets": usage.total_prompt_gets,
                "last_activity_at": usage.last_activity_at.isoformat() if usage.last_activity_at else None,
            }
            for usage, mcp in mcp_usage
        ],
        "tool_usage": [
            {
                "tool_id": tool.id,
                "tool_name": tool.name,
                "mcp_name": mcp.name,
                "total_calls": usage.total_calls,
                "first_called_at": usage.first_called_at.isoformat() if usage.first_called_at else None,
                "last_called_at": usage.last_called_at.isoformat() if usage.last_called_at else None,
            }
            for usage, tool, mcp in tool_usage
        ],
        "resource_usage": [
            {
                "resource_id": resource.id,
                "resource_name": resource.name,
                "resource_uri": resource.uri,
                "mcp_name": mcp.name,
                "total_reads": usage.total_reads,
                "first_read_at": usage.first_read_at.isoformat() if usage.first_read_at else None,
                "last_read_at": usage.last_read_at.isoformat() if usage.last_read_at else None,
            }
            for usage, resource, mcp in resource_usage
        ],
        "prompt_usage": [
            {
                "prompt_id": prompt.id,
                "prompt_name": prompt.name,
                "mcp_name": mcp.name,
                "total_gets": usage.total_gets,
                "first_got_at": usage.first_got_at.isoformat() if usage.first_got_at else None,
                "last_got_at": usage.last_got_at.isoformat() if usage.last_got_at else None,
            }
            for usage, prompt, mcp in prompt_usage
        ],
    } 