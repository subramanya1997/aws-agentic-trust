from __future__ import annotations

import uuid
import hashlib
from typing import Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete as sqldelete, and_

from agentictrust.backend.core.exceptions import NotFoundError, DatabaseError
from agentictrust.backend.data.models.agent import Agent
from agentictrust.backend.data.models.tool import Tool
from agentictrust.backend.data.models.resource import Resource
from agentictrust.backend.data.models.prompt import Prompt
from agentictrust.backend.data.models.mcp import MCP
from agentictrust.backend.schemas.agent import AgentCreate, AgentResponse, AgentListResponse


class Engine:  # noqa: D401  (simple façade)
    """High-level operations for *Agent* identities.

    Mirrors the pattern used by *core.mcp.engine.Engine* so that API endpoints
    remain thin controllers that delegate to this façade.
    """

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _hash_secret(secret: str) -> str:
        """Create a SHA-256 hash suitable for storage in DB."""
        return hashlib.sha256(secret.encode()).hexdigest()

    # ---------------------------------------------------------------------
    # Registration / creation
    # ---------------------------------------------------------------------

    @staticmethod
    async def register(db: AsyncSession, payload: AgentCreate) -> Tuple[Agent, str]:
        """Register a new agent and *return* the plaintext secret.

        Returns (agent_row, client_secret).
        """
        # Validate capability IDs ------------------------------------------------
        await Engine._verify_capability_ids(db, payload)

        client_id = str(uuid.uuid4())
        client_secret = uuid.uuid4().hex  # show once
        secret_hash = Engine._hash_secret(client_secret)

        agent = Agent(
            client_id=client_id,
            client_secret_hash=secret_hash,
            name=payload.name,
            description=payload.description,
            allowed_tool_ids=list(payload.tool_ids),
            allowed_resource_ids=list(payload.resource_ids),
            allowed_prompt_ids=list(payload.prompt_ids),
        )

        try:
            db.add(agent)
            await db.commit()
            await db.refresh(agent)
        except Exception as exc:
            await db.rollback()
            raise DatabaseError(str(exc)) from exc

        return agent, client_secret

    # ---------------------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------------------

    @staticmethod
    async def authenticate(db: AsyncSession, client_id: str, secret: str) -> Agent:
        agent = (
            await db.execute(select(Agent).where(Agent.client_id == client_id))
        ).scalar_one_or_none()
        if not agent or not agent.verify_secret(secret):
            raise NotFoundError("Agent", client_id)
        return agent

    # ---------------------------------------------------------------------
    # CRUD helpers
    # ---------------------------------------------------------------------

    @staticmethod
    async def get(db: AsyncSession, agent_id: str) -> Agent | None:
        return (
            await db.execute(select(Agent).where(Agent.id == agent_id))
        ).scalar_one_or_none()

    @staticmethod
    async def delete(db: AsyncSession, agent_id: str) -> None:
        await db.execute(sqldelete(Agent).where(Agent.id == agent_id))
        await db.commit()

    @staticmethod
    async def update(db: AsyncSession, agent: Agent, updates) -> Agent:
        """Update an existing agent with new metadata and/or capability lists.
        
        Args:
            db: Database session
            agent: The agent instance to update
            updates: AgentUpdate payload with fields to update
            
        Returns:
            Updated agent instance
        """
        
        # Validate capability IDs if any are provided
        if updates.tool_ids is not None or updates.resource_ids is not None or updates.prompt_ids is not None:
            # Create a temporary payload for validation
            temp_payload = AgentCreate(
                tool_ids=updates.tool_ids if updates.tool_ids is not None else [],
                resource_ids=updates.resource_ids if updates.resource_ids is not None else [],
                prompt_ids=updates.prompt_ids if updates.prompt_ids is not None else []
            )
            await Engine._verify_capability_ids(db, temp_payload)
        
        # Update fields that are provided (not None)
        if updates.name is not None:
            agent.name = updates.name
        if updates.description is not None:
            agent.description = updates.description
        if updates.tool_ids is not None:
            agent.allowed_tool_ids = list(updates.tool_ids)
        if updates.resource_ids is not None:
            agent.allowed_resource_ids = list(updates.resource_ids)
        if updates.prompt_ids is not None:
            agent.allowed_prompt_ids = list(updates.prompt_ids)
        
        try:
            await db.commit()
            await db.refresh(agent)
        except Exception as exc:
            await db.rollback()
            raise DatabaseError(str(exc)) from exc
            
        return agent

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Agent], int]:
        total = (
            await db.execute(select(func.count()).select_from(Agent))
        ).scalar()
        rows = (
            await db.execute(select(Agent).order_by(Agent.created_at.desc()).offset(skip).limit(limit))
        ).scalars().all()
        return rows, total

    # ------------------------------------------------------------------
    # Capabilities helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def list_tools(db: AsyncSession, agent: Agent):
        if not agent.tools:
            return []
        rows = (
            await db.execute(select(Tool).where(Tool.id.in_(agent.tools)))
        ).scalars().all()
        return [t.to_dict() for t in rows]

    @staticmethod
    async def list_resources(db: AsyncSession, agent: Agent):
        if not agent.resources:
            return []
        rows = (
            await db.execute(select(Resource).where(Resource.id.in_(agent.resources)))
        ).scalars().all()
        return [r.to_dict() for r in rows]

    @staticmethod
    async def list_prompts(db: AsyncSession, agent: Agent):
        if not agent.prompts:
            return []
        rows = (
            await db.execute(select(Prompt).where(Prompt.id.in_(agent.prompts)))
        ).scalars().all()
        return [p.to_dict() for p in rows]

    # ------------------------------------------------------------------
    # Internal validation
    # ------------------------------------------------------------------

    @staticmethod
    async def _verify_capability_ids(db: AsyncSession, payload: AgentCreate) -> None:
        """Ensure all referenced tool/resource/prompt IDs exist in DB."""

        # Tools
        if payload.tool_ids:
            tools_found = (
                await db.execute(select(Tool.id).where(Tool.id.in_(payload.tool_ids)))
            ).scalars().all()
            missing = set(payload.tool_ids) - set(tools_found)
            if missing:
                raise DatabaseError(f"Unknown tool IDs: {', '.join(missing)}")

        # Resources
        if payload.resource_ids:
            res_found = (
                await db.execute(select(Resource.id).where(Resource.id.in_(payload.resource_ids)))
            ).scalars().all()
            missing = set(payload.resource_ids) - set(res_found)
            if missing:
                raise DatabaseError(f"Unknown resource IDs: {', '.join(missing)}")

        # Prompts
        if payload.prompt_ids:
            prom_found = (
                await db.execute(select(Prompt.id).where(Prompt.id.in_(payload.prompt_ids)))
            ).scalars().all()
            missing = set(payload.prompt_ids) - set(prom_found)
            if missing:
                raise DatabaseError(f"Unknown prompt IDs: {', '.join(missing)}")

    # ------------------------------------------------------------------
    # High-level helpers used by API layer (moved from routes)
    # ------------------------------------------------------------------

    @staticmethod
    def agent_basic_response(agent: Agent) -> AgentResponse:
        """Return an AgentResponse with *no* capability objects populated."""

        data = {
            **agent.to_dict(),
            "tool_ids": agent.allowed_tool_ids or [],
            "resource_ids": agent.allowed_resource_ids or [],
            "prompt_ids": agent.allowed_prompt_ids or [],
            "tools": [],
            "resources": [],
            "prompts": [],
        }
        return AgentResponse(**data)

    # ------------------------------------------------------------------
    # Paginated list + capability enrichment (previously in route)
    # ------------------------------------------------------------------

    @staticmethod
    async def list_detailed(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> AgentListResponse:
        """Return paginated list of agents with enriched capability metadata.

        This mirrors the logic previously implemented directly in the FastAPI
        handler but lives here so that *all* DB interaction remains in the
        core layer.  Where feasible we rely on SQL conditions to limit data
        transferred to Python.
        """

        # Retrieve page of agents and total count (reuse existing helper)
        rows, total = await Engine.list(db, skip=skip, limit=limit)

        if not rows:
            return AgentListResponse(items=[], total=total, page=(skip // limit) + 1, size=limit)

        # -----------------------------------------------------------------
        # Bulk-collect capability IDs so we can fetch metadata in one query
        # per capability type.
        # -----------------------------------------------------------------
        all_tool_ids = {tid for a in rows for tid in (a.allowed_tool_ids or [])}
        all_resource_ids = {rid for a in rows for rid in (a.allowed_resource_ids or [])}
        all_prompt_ids = {pid for a in rows for pid in (a.allowed_prompt_ids or [])}

        # -----------------------------------------------------------------
        # Fetch capability rows only if we have IDs to resolve.
        # -----------------------------------------------------------------
        tool_rows = []
        resource_rows = []
        prompt_rows = []

        if all_tool_ids:
            tool_rows = (
                await db.execute(select(Tool.id, Tool.name, Tool.mcp_id).where(Tool.id.in_(all_tool_ids)))
            ).all()

        if all_resource_ids:
            resource_rows = (
                await db.execute(
                    select(Resource.id, Resource.name, Resource.mcp_id).where(Resource.id.in_(all_resource_ids))
                )
            ).all()

        if all_prompt_ids:
            prompt_rows = (
                await db.execute(select(Prompt.id, Prompt.name, Prompt.mcp_id).where(Prompt.id.in_(all_prompt_ids)))
            ).all()

        # -----------------------------------------------------------------
        # Build MCP-id → name map so we can include it in the capability meta.
        # -----------------------------------------------------------------
        mcp_ids_set = {row.mcp_id for row in (tool_rows + resource_rows + prompt_rows) if row.mcp_id}
        mcp_name_map = {}
        if mcp_ids_set:
            mcp_rows = await db.execute(select(MCP.id, MCP.name).where(MCP.id.in_(mcp_ids_set)))
            mcp_name_map = {r.id: r.name for r in mcp_rows}

        # Capability lookup maps keyed by ID --------------------------------
        tool_map = {
            r.id: {"id": r.id, "mcp_id": r.mcp_id, "mcp_name": mcp_name_map.get(r.mcp_id), "name": r.name}
            for r in tool_rows
        }
        resource_map = {
            r.id: {"id": r.id, "mcp_id": r.mcp_id, "mcp_name": mcp_name_map.get(r.mcp_id), "name": r.name}
            for r in resource_rows
        }
        prompt_map = {
            r.id: {"id": r.id, "mcp_id": r.mcp_id, "mcp_name": mcp_name_map.get(r.mcp_id), "name": r.name}
            for r in prompt_rows
        }

        # -----------------------------------------------------------------
        # Build AgentResponse items
        # -----------------------------------------------------------------
        response_items = []
        for a in rows:
            payload = {
                **a.to_dict(),
                "tool_ids": a.allowed_tool_ids or [],
                "resource_ids": a.allowed_resource_ids or [],
                "prompt_ids": a.allowed_prompt_ids or [],
                "tools": [tool_map[tid] for tid in a.allowed_tool_ids if tid in tool_map],
                "resources": [resource_map[rid] for rid in a.allowed_resource_ids if rid in resource_map],
                "prompts": [prompt_map[pid] for pid in a.allowed_prompt_ids if pid in prompt_map],
            }
            response_items.append(AgentResponse(**payload))

        return AgentListResponse(
            items=response_items,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
        )

    # ------------------------------------------------------------------
    # Summary statistics (moved from route)
    # ------------------------------------------------------------------

    @staticmethod
    async def status_summary(db: AsyncSession) -> dict:  # noqa: C901 (complexity ok for aggregation)
        """Compute summary statistics for agents and their capabilities."""

        from datetime import datetime, timedelta, timezone
        from sqlalchemy import func

        # Total agents ---------------------------------------------------
        total_agents = (await db.execute(select(func.count()).select_from(Agent))).scalar()

        # Fetch capability lists for all agents in one query -------------
        agent_caps = (
            await db.execute(
                select(Agent.allowed_tool_ids, Agent.allowed_resource_ids, Agent.allowed_prompt_ids)
            )
        ).all()

        # Aggregate capability IDs in Python (JSON columns make SQL aggregation tricky)
        unique_tool_ids: set[str] = set()
        unique_resource_ids: set[str] = set()
        unique_prompt_ids: set[str] = set()

        total_tools_assigned = 0
        total_resources_assigned = 0
        total_prompts_assigned = 0

        for row in agent_caps:
            tools = row.allowed_tool_ids or []
            resources = row.allowed_resource_ids or []
            prompts = row.allowed_prompt_ids or []

            unique_tool_ids.update(tools)
            unique_resource_ids.update(resources)
            unique_prompt_ids.update(prompts)

            total_tools_assigned += len(tools)
            total_resources_assigned += len(resources)
            total_prompts_assigned += len(prompts)

        total_capabilities_assigned = total_tools_assigned + total_resources_assigned + total_prompts_assigned

        # Average per agent (avoid division by zero)
        avg_capabilities = total_capabilities_assigned / total_agents if total_agents else 0

        # Count available capabilities via cheap COUNT(*).
        total_tools_available = (await db.execute(select(func.count()).select_from(Tool))).scalar()
        total_resources_available = (await db.execute(select(func.count()).select_from(Resource))).scalar()
        total_prompts_available = (await db.execute(select(func.count()).select_from(Prompt))).scalar()

        # Trend calculations (last 7 days vs previous 7 days)
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # Recent registrations (last 7 days)
        recent_count = (
            await db.execute(select(func.count()).select_from(Agent).where(Agent.created_at >= week_ago))
        ).scalar()
        
        # Previous week registrations (8-14 days ago)
        previous_week_count = (
            await db.execute(
                select(func.count()).select_from(Agent)
                .where(and_(Agent.created_at >= two_weeks_ago, Agent.created_at < week_ago))
            )
        ).scalar()
        
        # Calculate trend percentage
        if previous_week_count > 0:
            trend_percentage = ((recent_count - previous_week_count) / previous_week_count) * 100
        else:
            trend_percentage = 100.0 if recent_count > 0 else 0.0

        return {
            "total": total_agents,
            "capabilities": {
                "tools": len(unique_tool_ids),
                "resources": len(unique_resource_ids),
                "prompts": len(unique_prompt_ids),
                "total_unique": len(unique_tool_ids) + len(unique_resource_ids) + len(unique_prompt_ids),
                "available": {
                    "tools": total_tools_available,
                    "resources": total_resources_available,
                    "prompts": total_prompts_available,
                },
            },
            "avg_capabilities_per_agent": round(avg_capabilities, 1),
            "recent_registrations": recent_count,
            "trends": {
                "recent_registrations": recent_count,
                "previous_week_registrations": previous_week_count,
                "trend_percentage": round(trend_percentage, 1),
                "is_positive": trend_percentage >= 0,
            },
        } 