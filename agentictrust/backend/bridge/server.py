from __future__ import annotations

"""Agent-aware MCP Bridge Server

A multi-tenant MCP server that dynamically filters tools, resources, and prompts
based on authenticated agent credentials. Each agent sees only their permitted
subset of capabilities from the registered upstream MCP servers.
"""

import asyncio
import logging
import uuid
from typing import Any, Iterable, Sequence, Dict, List, Optional
from contextlib import asynccontextmanager
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic.networks import AnyUrl
from sqlalchemy import select

from mcp.server.fastmcp.server import FastMCP, _convert_to_content
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.types import (
    EmbeddedResource,
    GetPromptResult,
    ImageContent,
    TextContent,
    Tool as MCPTool,
    Resource as MCPResource,
    Prompt as MCPPrompt,
)
from mcp.client.session_group import (
    ClientSessionGroup,
    ServerParameters,
    SseServerParameters,
    StreamableHttpParameters,
)
from mcp.client.stdio import StdioServerParameters

# Backend imports
from agentictrust.backend.config.database import AsyncSessionLocal
from agentictrust.backend.data.models.mcp import MCP as MCPModel
from agentictrust.backend.core.agent import Engine as AgentEngine
from agentictrust.backend.data.models.agent import Agent
from agentictrust.backend.data.models.usage_tracking import (
    AgentMCPUsage,
    AgentToolUsage,
    AgentResourceUsage,
    AgentPromptUsage,
)
from agentictrust.backend.data.models.tool import Tool
from agentictrust.backend.data.models.resource import Resource
from agentictrust.backend.data.models.prompt import Prompt
from agentictrust.backend.data.models.logs import LogEntry

logger = logging.getLogger(__name__)

# Debug file logging (bypasses logging.disable)
DEBUG_LOG_PATH = Path.home() / ".agentictrust" / "bridge_debug.log"
DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def debug_log(message: str) -> None:
    """Write debug messages directly to file, bypassing logging system."""
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        with open(DEBUG_LOG_PATH, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
            f.flush()
    except Exception:
        pass  # Silently fail to avoid breaking the main flow

# Helper context manager for acquiring DB sessions
@asynccontextmanager
async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session

class AgentAwareMCPBridge(FastMCP):
    """Multi-tenant MCP server that filters capabilities by authenticated agent."""

    def __init__(
        self,
        *,
        name: str | None = "Agent-Aware MCP Bridge",
        instructions: str | None = (
            "This server provides access to tools, resources, and prompts "
            "based on your authenticated agent credentials."
        ),
        **settings: Any,
    ) -> None:
        debug_log("=== AgentAwareMCPBridge INIT ===")
        # Store current agent context
        self._current_agent: Agent | None = None
        self._upstream_group: ClientSessionGroup | None = None
        
        @asynccontextmanager
        async def _bridge_lifespan(_app):
            # Initialize upstream connections during lifespan
            self._upstream_group = ClientSessionGroup()
            await self._upstream_group.__aenter__()
            
            connected_mcps = []  # Track which MCPs we successfully connected to
            
            # Connect to all registered MCP servers (not just active ones)
            async with get_async_session() as db:
                mcps = (await db.execute(
                    select(MCPModel).where(MCPModel.status.in_(["registered", "active"]))
                )).scalars().all()
                
                for mcp in mcps:
                    try:
                        server_params = self._server_params_from_model(mcp)
                        await self._upstream_group.connect_to_server(server_params)
                        
                        # Update MCP connection status
                        mcp.increment_connection()
                        connected_mcps.append(mcp.id)  # Track successful connection
                        await db.commit()
                        
                        logger.info(f"Connected to upstream MCP: {mcp.name} (instances: {mcp.connected_instances}, status: {mcp.status})")
                    except Exception as e:
                        logger.warning(f"Failed to connect to MCP {mcp.name}: {e}")
            
            try:
                yield
            finally:
                # Properly disconnect and update status
                if self._upstream_group:
                    await self._upstream_group.__aexit__(None, None, None)
                
                # Decrement connection counts and update status for connected MCPs
                async with get_async_session() as db:
                    for mcp_id in connected_mcps:
                        mcp = (await db.execute(
                            select(MCPModel).where(MCPModel.id == mcp_id)
                        )).scalar_one_or_none()
                        
                        if mcp:
                            mcp.decrement_connection()
                            logger.info(f"Disconnected from MCP: {mcp.name} (instances: {mcp.connected_instances}, status: {mcp.status})")
                    
                    await db.commit()

        settings.setdefault("lifespan", _bridge_lifespan)
        
        super().__init__(
            name=name,
            instructions=instructions,
            **settings
        )

    def _server_params_from_model(self, mcp: MCPModel) -> ServerParameters:
        """Convert DB MCP model into ServerParameters."""
        if mcp.server_type == "command":
            return StdioServerParameters(
                command=mcp.command,
                args=mcp.args_list,
                env=mcp.env_dict,
            )
        elif mcp.server_type == "sse":
            return SseServerParameters(url=mcp.url)
        else:
            return StreamableHttpParameters(url=mcp.url)

    async def _authenticate_agent(self, client_id: str, client_secret: str) -> Agent | None:
        """Authenticate agent credentials and return Agent model."""
        try:
            async with get_async_session() as db:
                agent = await AgentEngine.authenticate(db, client_id, client_secret)
                return agent
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            return None

    def set_current_agent(self, agent: Agent) -> None:
        """Set the current authenticated agent for request context."""
        self._current_agent = agent
        debug_log(f"Current agent set to: {agent.name} ({agent.id})")

    async def _track_agent_connection(self, agent: Agent) -> None:
        """Track agent connection to MCP servers."""
        if not self._upstream_group:
            return
            
        async with get_async_session() as db:
            # Get all connected MCPs
            mcps = (await db.execute(
                select(MCPModel).where(MCPModel.connected_instances > 0)
            )).scalars().all()
            
            for mcp in mcps:
                # Get or create usage tracking record
                usage = (await db.execute(
                    select(AgentMCPUsage).where(
                        AgentMCPUsage.agent_id == agent.id,
                        AgentMCPUsage.mcp_id == mcp.id
                    )
                )).scalar_one_or_none()
                
                if not usage:
                    usage = AgentMCPUsage(
                        id=str(uuid.uuid4()),
                        agent_id=agent.id,
                        mcp_id=mcp.id
                    )
                    db.add(usage)
                
                usage.connect()
                
            await db.commit()

    async def _track_agent_disconnection(self, agent: Agent) -> None:
        """Track agent disconnection from MCP servers."""
        async with get_async_session() as db:
            # Mark all agent connections as disconnected
            usages = (await db.execute(
                select(AgentMCPUsage).where(
                    AgentMCPUsage.agent_id == agent.id,
                    AgentMCPUsage.is_connected == "true"
                )
            )).scalars().all()
            
            for usage in usages:
                usage.disconnect()
                
            await db.commit()

    async def _track_tool_usage(self, agent: Agent, tool_name: str) -> None:
        """Track tool usage by agent."""
        async with get_async_session() as db:
            # Find the tool
            tool = (await db.execute(
                select(Tool).where(Tool.name == tool_name)
            )).scalar_one_or_none()
            
            if not tool:
                return
                
            # Update MCP usage
            mcp_usage = (await db.execute(
                select(AgentMCPUsage).where(
                    AgentMCPUsage.agent_id == agent.id,
                    AgentMCPUsage.mcp_id == tool.mcp_id
                )
            )).scalar_one_or_none()
            
            if mcp_usage:
                mcp_usage.record_tool_call()
            
            # Update tool-specific usage
            tool_usage = (await db.execute(
                select(AgentToolUsage).where(
                    AgentToolUsage.agent_id == agent.id,
                    AgentToolUsage.tool_id == tool.id
                )
            )).scalar_one_or_none()
            
            if not tool_usage:
                tool_usage = AgentToolUsage(
                    id=str(uuid.uuid4()),
                    agent_id=agent.id,
                    tool_id=tool.id
                )
                db.add(tool_usage)
            
            tool_usage.record_call()
            await db.commit()

    async def _track_resource_usage(self, agent: Agent, resource_uri: str) -> None:
        """Track resource usage by agent."""
        async with get_async_session() as db:
            # Find the resource
            resource = (await db.execute(
                select(Resource).where(Resource.uri == resource_uri)
            )).scalar_one_or_none()
            
            if not resource:
                return
                
            # Update MCP usage
            mcp_usage = (await db.execute(
                select(AgentMCPUsage).where(
                    AgentMCPUsage.agent_id == agent.id,
                    AgentMCPUsage.mcp_id == resource.mcp_id
                )
            )).scalar_one_or_none()
            
            if mcp_usage:
                mcp_usage.record_resource_read()
            
            # Update resource-specific usage
            resource_usage = (await db.execute(
                select(AgentResourceUsage).where(
                    AgentResourceUsage.agent_id == agent.id,
                    AgentResourceUsage.resource_id == resource.id
                )
            )).scalar_one_or_none()
            
            if not resource_usage:
                resource_usage = AgentResourceUsage(
                    id=str(uuid.uuid4()),
                    agent_id=agent.id,
                    resource_id=resource.id
                )
                db.add(resource_usage)
            
            resource_usage.record_read()
            await db.commit()

    async def _track_prompt_usage(self, agent: Agent, prompt_name: str) -> None:
        """Track prompt usage by agent."""
        async with get_async_session() as db:
            # Find the prompt
            prompt = (await db.execute(
                select(Prompt).where(Prompt.name == prompt_name)
            )).scalar_one_or_none()
            
            if not prompt:
                return
                
            # Update MCP usage
            mcp_usage = (await db.execute(
                select(AgentMCPUsage).where(
                    AgentMCPUsage.agent_id == agent.id,
                    AgentMCPUsage.mcp_id == prompt.mcp_id
                )
            )).scalar_one_or_none()
            
            if mcp_usage:
                mcp_usage.record_prompt_get()
            
            # Update prompt-specific usage
            prompt_usage = (await db.execute(
                select(AgentPromptUsage).where(
                    AgentPromptUsage.agent_id == agent.id,
                    AgentPromptUsage.prompt_id == prompt.id
                )
            )).scalar_one_or_none()
            
            if not prompt_usage:
                prompt_usage = AgentPromptUsage(
                    id=str(uuid.uuid4()),
                    agent_id=agent.id,
                    prompt_id=prompt.id
                )
                db.add(prompt_usage)
            
            prompt_usage.record_get()
            await db.commit()

    async def _authenticate_from_env(self) -> Agent | None:
        """Authenticate agent from environment variables (for stdio transport)."""
        client_id = os.environ.get("MCP_CLIENT_ID")
        client_secret = os.environ.get("API_KEY") or os.environ.get("MCP_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            logger.warning("Missing MCP_CLIENT_ID or API_KEY/MCP_CLIENT_SECRET environment variables")
            return None
            
        try:
            async with get_async_session() as db:
                agent = await AgentEngine.authenticate(db, client_id, client_secret)
                logger.info(f"Authenticated agent from environment: {agent.name} ({agent.client_id})")
                return agent
        except Exception as e:
            logger.warning(f"Environment authentication failed: {e}")
            return None

    async def _get_agent_tools(self) -> List[Dict[str, Any]]:
        """Get tools available to current agent."""
        if not self._current_agent:
            return []
        
        async with get_async_session() as db:
            # Refresh agent data from database to get latest permissions
            debug_log(f"Refreshing agent permissions from database for agent {self._current_agent.id}")
            fresh_agent = await AgentEngine.get(db, self._current_agent.id)
            if not fresh_agent:
                logger.warning(f"Agent {self._current_agent.id} no longer exists in database")
                debug_log(f"ERROR: Agent {self._current_agent.id} not found in database")
                return []
            
            debug_log(f"Agent {fresh_agent.id} has tool_ids: {fresh_agent.allowed_tool_ids}")
            return await AgentEngine.list_tools(db, fresh_agent)

    async def _get_agent_resources(self) -> List[Dict[str, Any]]:
        """Get resources available to current agent."""
        if not self._current_agent:
            return []
        
        async with get_async_session() as db:
            # Refresh agent data from database to get latest permissions
            fresh_agent = await AgentEngine.get(db, self._current_agent.id)
            if not fresh_agent:
                logger.warning(f"Agent {self._current_agent.id} no longer exists in database")
                return []
            
            return await AgentEngine.list_resources(db, fresh_agent)

    async def _get_agent_prompts(self) -> List[Dict[str, Any]]:
        """Get prompts available to current agent."""
        if not self._current_agent:
            return []
        
        async with get_async_session() as db:
            # Refresh agent data from database to get latest permissions
            fresh_agent = await AgentEngine.get(db, self._current_agent.id)
            if not fresh_agent:
                logger.warning(f"Agent {self._current_agent.id} no longer exists in database")
                return []
            
            return await AgentEngine.list_prompts(db, fresh_agent)

    # MCP Protocol Implementation
    
    async def list_tools(self) -> list[MCPTool]:
        """Return tools filtered by current agent permissions."""
        try:
            agent_tools = await self._get_agent_tools()
            return [
                MCPTool(
                    name=tool["name"],
                    description=tool.get("description"),
                    inputSchema=tool.get("input_schema", {}),
                )
                for tool in agent_tools
            ]
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def _log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        severity: str = "info",
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Persist a detailed LogEntry to the database.

        Parameters
        ----------
        event_type: str
            A string describing the event type (e.g. `call_tool`, `tool_result`).
        data: Dict[str, Any]
            JSON-serialisable dictionary containing event metadata / payload.
        severity: str, default ``info``
            Log severity level. One of ``debug``, ``info``, ``warning``, ``error``, ``critical``.
        correlation_id: Optional[str]
            Identifier used to correlate request/response pairs.
        session_id: Optional[str]
            Session identifier if applicable (e.g. SSE session).
        """

        debug_log(f"_log_event: type={event_type}, correlation_id={correlation_id}, data_keys={list(data.keys()) if data else []}")
        
        try:
            async with get_async_session() as db:
                log_entry = LogEntry(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type=event_type,
                    data=data,
                    correlation_id=correlation_id,
                    session_id=session_id,
                    source="bridge",
                    severity=severity,
                )
                db.add(log_entry)
                await db.commit()
                debug_log(f"_log_event: Successfully persisted {event_type} to database")
        except Exception as e:
            # Do not crash main flow if logging fails – just log to std logger
            debug_log(f"_log_event ERROR: Failed to persist {event_type}: {e}")
            logger.error(f"Failed to persist log entry ({event_type}): {e}")

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Call a tool if agent has permission."""
        debug_log(f"=== call_tool START: {name} with args: {arguments}")
        
        # Create correlation id for request/response pair early
        corr_id = str(uuid.uuid4())
        debug_log(f"Correlation ID: {corr_id}")
        
        if not self._current_agent or not self._upstream_group:
            debug_log(f"ERROR: No agent or upstream group. Agent: {self._current_agent}, Group: {self._upstream_group}")
            raise ValueError("No authenticated agent or upstream connections")

        debug_log(f"Current agent: {self._current_agent.name} ({self._current_agent.id})")

        # Log the incoming tool call attempt (before permission check)
        debug_log("Logging call_tool event...")
        await self._log_event(
            "call_tool",
            {
                "tool_name": name,
                "arguments": arguments,
                "agent_id": self._current_agent.id if self._current_agent else None,
                "agent_name": self._current_agent.name if self._current_agent else None,
            },
            correlation_id=corr_id,
        )
        debug_log("call_tool event logged successfully")

        # Verify agent has access to this tool
        agent_tools = await self._get_agent_tools()
        tool_names = {t["name"] for t in agent_tools}
        debug_log(f"Agent has access to tools: {tool_names}")
        
        if name not in tool_names:
            debug_log(f"ERROR: Tool '{name}' not in permitted tools")
            # Log the denial as a tool_error event
            await self._log_event(
                "tool_error",
                {
                    "tool_name": name,
                    "error": f"Tool '{name}' not permitted for this agent",
                    "error_type": "access_denied",
                    "agent_id": self._current_agent.id if self._current_agent else None,
                },
                severity="warning",
                correlation_id=corr_id,
            )
            raise ValueError(f"Tool '{name}' not permitted for this agent")

        # Call through upstream group
        try:
            # Re-verify agent still has access to this tool before making the upstream call
            debug_log(f"Re-verifying agent access to tool '{name}' before upstream call...")
            current_agent_tools = await self._get_agent_tools()
            current_tool_names = {t["name"] for t in current_agent_tools}
            
            if name not in current_tool_names:
                debug_log(f"ERROR: Tool '{name}' access revoked - not forwarding to upstream")
                # Log the revoked access as a tool_error event
                await self._log_event(
                    "tool_error",
                    {
                        "tool_name": name,
                        "error": f"Tool '{name}' access has been revoked for this agent",
                        "error_type": "access_revoked",
                        "agent_id": self._current_agent.id if self._current_agent else None,
                    },
                    severity="warning",
                    correlation_id=corr_id,
                )
                raise ValueError(f"Tool '{name}' access has been revoked for this agent")
            
            debug_log(f"Access verified. Calling upstream tool '{name}'...")
            # Add timeout to prevent hanging tool calls
            result = await asyncio.wait_for(
                self._upstream_group.call_tool(name, arguments),
                timeout=30.0  # 30 second timeout
            )
            debug_log(f"Tool call returned. Result type: {type(result)}")
            
            # Track tool usage - wrap in try/except to ensure logging continues
            try:
                debug_log("Tracking tool usage...")
                await self._track_tool_usage(self._current_agent, name)
                debug_log("Tool usage tracked successfully")
            except Exception as track_error:
                # Log but don't fail the whole operation
                debug_log(f"ERROR tracking tool usage: {track_error}")
                logger.warning(f"Failed to track tool usage for '{name}': {track_error}")

            # Log the tool result (a lightweight representation)
            try:
                debug_log(f"Extracting sample output. Has content: {hasattr(result, 'content')}")
                if hasattr(result, "content"):
                    debug_log(f"Content type: {type(result.content)}, length: {len(result.content) if hasattr(result.content, '__len__') else 'N/A'}")
                
                # Convert TextContent/ImageContent objects to dictionaries for JSON serialization
                sample_output = None
                if hasattr(result, "content") and result.content:
                    first_item = result.content[0]
                    if hasattr(first_item, "type") and hasattr(first_item, "text"):
                        # TextContent object - convert to dict
                        sample_output = [{"type": first_item.type, "text": first_item.text[:500] if first_item.text else ""}]  # Limit text to 500 chars
                    elif hasattr(first_item, "type") and hasattr(first_item, "data"):
                        # ImageContent object - convert to dict
                        sample_output = [{"type": first_item.type, "data": "...image data..."}]  # Don't store actual image data
                    else:
                        # Unknown type - try to convert to string
                        sample_output = [{"type": "unknown", "data": str(first_item)[:500]}]
                
                debug_log(f"Sample output extracted: {sample_output}")
            except Exception as sample_error:
                debug_log(f"ERROR extracting sample: {sample_error}")
                logger.warning(f"Failed to extract sample output: {sample_error}")
                sample_output = None

            # Always try to log the result
            debug_log("Logging tool_result event...")
            await self._log_event(
                "tool_result",
                {
                    "tool_name": name,
                    "output_sample": sample_output,
                    "agent_id": self._current_agent.id if self._current_agent else None,
                    "agent_name": self._current_agent.name if self._current_agent else None,
                },
                correlation_id=corr_id,
            )
            debug_log("tool_result event logged successfully")
            
            debug_log("=== call_tool END: Success")
            return _convert_to_content(result.content)
        except asyncio.TimeoutError:
            error_msg = f"Tool '{name}' timed out after 30 seconds"
            logger.error(error_msg)
            await self._log_event(
                "tool_error",
                {
                    "tool_name": name,
                    "error": error_msg,
                    "error_type": "timeout",
                    "agent_id": self._current_agent.id if self._current_agent else None,
                },
                severity="error",
                correlation_id=corr_id,
            )
            raise ValueError(error_msg)
        except ValueError as e:
            # Handle permission-related errors (including revoked access)
            error_msg = str(e)
            logger.warning(f"Tool access denied: {error_msg}")
            await self._log_event(
                "tool_error",
                {
                    "tool_name": name,
                    "error": error_msg,
                    "error_type": "access_denied",
                    "agent_id": self._current_agent.id if self._current_agent else None,
                },
                severity="warning",
                correlation_id=corr_id,
            )
            raise  # Re-raise the ValueError as-is
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            await self._log_event(
                "tool_error",
                {
                    "tool_name": name,
                    "error": str(e),
                    "error_type": "execution_error",
                    "agent_id": self._current_agent.id if self._current_agent else None,
                },
                severity="error",
                correlation_id=corr_id,
            )
            raise ValueError(f"Tool execution failed: {e}")

    async def list_resources(self) -> list[MCPResource]:
        """Return resources filtered by current agent permissions."""
        try:
            agent_resources = await self._get_agent_resources()
            return [
                MCPResource(
                    uri=resource["uri"],
                    name=resource["name"],
                    description=resource.get("description"),
                    mimeType=resource.get("mime_type"),
                )
                for resource in agent_resources
            ]
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            return []

    async def read_resource(self, uri: str | AnyUrl) -> Iterable[ReadResourceContents]:
        """Read a resource if agent has permission."""
        if not self._current_agent or not self._upstream_group:
            raise ValueError("No authenticated agent or upstream connections")

        # Verify agent has access to this resource
        agent_resources = await self._get_agent_resources()
        resource_uris = {r["uri"] for r in agent_resources}
        
        if str(uri) not in resource_uris:
            raise ValueError(f"Resource '{uri}' not permitted for this agent")

        corr_id = str(uuid.uuid4())
        await self._log_event(
            "read_resource",
            {
                "resource_uri": str(uri),
                "agent_id": self._current_agent.id if self._current_agent else None,
            },
            correlation_id=corr_id,
        )

        # Read through upstream group
        try:
            # Find the session that has this resource
            for session, comp_names in self._upstream_group._sessions.items():
                for res_name in comp_names.resources:
                    resource = self._upstream_group.resources[res_name]
                    if str(resource.uri) == str(uri):
                        upstream_result = await session.read_resource(resource.uri)
                        
                        # Track resource usage
                        await self._track_resource_usage(self._current_agent, str(uri))
                        
                        # Convert to ReadResourceContents
                        from mcp.types import TextResourceContents, BlobResourceContents
                        import base64
                        
                        decoded = []
                        for content in upstream_result.contents:
                            if isinstance(content, TextResourceContents):
                                decoded.append(ReadResourceContents(
                                    content=content.text, 
                                    mime_type=content.mimeType
                                ))
                            elif isinstance(content, BlobResourceContents):
                                raw = base64.b64decode(content.blob)
                                decoded.append(ReadResourceContents(
                                    content=raw, 
                                    mime_type=content.mimeType
                                ))
                        return decoded

                        # Log output size for analysis (to avoid storing raw data)
                        await self._log_event(
                            "resource_result",
                            {
                                "resource_uri": str(uri),
                                "result_size": len(decoded),
                                "agent_id": self._current_agent.id if self._current_agent else None,
                            },
                            correlation_id=corr_id,
                        )
            
            raise ValueError(f"Resource '{uri}' not found in upstream servers")
        except Exception as e:
            logger.error(f"Resource read failed: {e}")
            await self._log_event(
                "resource_error",
                {
                    "resource_uri": str(uri),
                    "error": str(e),
                    "agent_id": self._current_agent.id if self._current_agent else None,
                },
                severity="error",
                correlation_id=corr_id,
            )
            raise ValueError(f"Resource read failed: {e}")

    async def list_prompts(self) -> list[MCPPrompt]:
        """Return prompts filtered by current agent permissions."""
        try:
            agent_prompts = await self._get_agent_prompts()
            return [
                MCPPrompt(
                    name=prompt["name"],
                    description=prompt.get("description"),
                    arguments=prompt.get("arguments", []),
                )
                for prompt in agent_prompts
            ]
        except Exception as e:
            logger.error(f"Failed to list prompts: {e}")
            return []

    async def get_prompt(self, name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
        """Get a prompt if agent has permission."""
        if not self._current_agent or not self._upstream_group:
            raise ValueError("No authenticated agent or upstream connections")

        # Verify agent has access to this prompt
        agent_prompts = await self._get_agent_prompts()
        prompt_names = {p["name"] for p in agent_prompts}
        
        if name not in prompt_names:
            raise ValueError(f"Prompt '{name}' not permitted for this agent")

        corr_id = str(uuid.uuid4())

        await self._log_event(
            "get_prompt",
            {
                "prompt_name": name,
                "arguments": arguments or {},
                "agent_id": self._current_agent.id if self._current_agent else None,
            },
            correlation_id=corr_id,
        )

        # Get through upstream group
        try:
            for session, comp_names in self._upstream_group._sessions.items():
                if name in comp_names.prompts:
                    result = await session.get_prompt(name, arguments)
                    
                    # Track prompt usage
                    await self._track_prompt_usage(self._current_agent, name)

                    await self._log_event(
                        "prompt_result",
                        {
                            "prompt_name": name,
                            "result_preview": result.prompt[:100] if hasattr(result, "prompt") else None,
                            "agent_id": self._current_agent.id if self._current_agent else None,
                        },
                        correlation_id=corr_id,
                    )
                    
                    return result
            
            raise ValueError(f"Prompt '{name}' not found in upstream servers")
        except Exception as e:
            logger.error(f"Prompt get failed: {e}")
            await self._log_event(
                "prompt_error",
                {
                    "prompt_name": name,
                    "error": str(e),
                    "agent_id": self._current_agent.id if self._current_agent else None,
                },
                severity="error",
                correlation_id=corr_id,
            )
            raise ValueError(f"Prompt get failed: {e}")

    def sse_app(self, mount_path: str | None = None):
        """Create SSE app with authentication middleware."""
        # Get the standard MCP SSE app
        app = super().sse_app(mount_path)
        
        # Add authentication middleware
        from .auth_middleware import BridgeAuthMiddleware
        app.add_middleware(BridgeAuthMiddleware, bridge_server=self)
        
        return app

    async def run_stdio_async(self) -> None:
        """Run the server using stdio transport with agent authentication."""
        debug_log("=== run_stdio_async START ===")
        
        # Ensure all loggers write to **stderr** so they don't corrupt the stdio JSON-RPC stream
        root_logger = logging.getLogger()
        # If any existing handlers point to stdout, redirect them to stderr
        for handler in list(root_logger.handlers):
            if getattr(handler, "stream", None) is sys.stdout:
                handler.stream = sys.stderr
        # In case no handler exists (unlikely), add one targeting stderr
        if not root_logger.handlers:
            logging.basicConfig(stream=sys.stderr, level=logging.INFO)

        # Authenticate agent from environment variables
        debug_log("Authenticating agent from environment...")
        agent = await self._authenticate_from_env()
        if not agent:
            debug_log("ERROR: Failed to authenticate agent for stdio transport")
            logger.error("Failed to authenticate agent for stdio transport")
            return
            
        debug_log(f"Authenticated agent: {agent.name} ({agent.id})")
        # Set the authenticated agent
        self.set_current_agent(agent)
        
        # Track agent connection
        await self._track_agent_connection(agent)
        
        # Run the stdio server
        from mcp.server.stdio import stdio_server
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self._mcp_server.run(
                    read_stream,
                    write_stream,
                    self._mcp_server.create_initialization_options(),
                )
        finally:
            # Track agent disconnection
            await self._track_agent_disconnection(agent) 