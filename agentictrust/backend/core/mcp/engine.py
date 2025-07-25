from __future__ import annotations

from typing import Tuple, List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete as sqldelete

from agentictrust.backend.schemas.mcp import (
    MCPBase,
    MCPUpdate,
    MCPServersConfig,
    ServerType,
)
from agentictrust.backend.data.models.mcp import MCP
from .utils import to_db_model, determine_server_type_from_json
from .transport import test_mcp_connection, MCPTransportError
from .persistence import persist_capabilities

# For capabilities retrieval
from agentictrust.backend.data.models.tool import Tool
from agentictrust.backend.data.models.resource import Resource
from agentictrust.backend.data.models.prompt import Prompt


class Engine:
    """High-level façade for all MCP operations (registration, update, test)."""

    # ------------------------------------------------------------------
    # Connectivity / introspection
    # ------------------------------------------------------------------

    @staticmethod
    async def test(config: MCPBase) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Connect and fetch capabilities (tools, resources, prompts)."""
        return await test_mcp_connection(config)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def persist_capabilities(
        db: AsyncSession,
        mcp_id: str,
        tools: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        prompts: List[Dict[str, Any]],
    ) -> None:
        await persist_capabilities(db, mcp_id, tools, resources, prompts)

    # ------------------------------------------------------------------
    # Registration & update
    # ------------------------------------------------------------------

    @staticmethod
    async def register(db: AsyncSession, config: MCPBase) -> MCP:
        """Full registration flow incl. capability persistence."""
        mcp = to_db_model(config)
        db.add(mcp)
        await db.commit()
        await db.refresh(mcp)
        try:
            tools, resources, prompts = await Engine.test(config)
            await Engine.persist_capabilities(db, mcp.id, tools, resources, prompts)
        except MCPTransportError:
            # swallow connectivity issues – registration still valid
            pass
        return mcp

    @staticmethod
    async def update(db: AsyncSession, mcp: MCP, updates: MCPUpdate) -> MCP:
        # apply updates
        for field, value in updates.dict(exclude_unset=True).items():
            if hasattr(mcp, field):
                setattr(mcp, field, value)
        await db.commit()
        await db.refresh(mcp)

        # Build interim config to retest if URL/SSE changed
        temp_config = MCPBase(
            name=mcp.name,
            server_type=mcp.server_type,  # type: ignore[arg-type]
            command=mcp.command,
            args=mcp.args,
            url=mcp.url,
            env=mcp.env,
            environment=mcp.environment,
        )
        try:
            tools, resources, prompts = await Engine.test(temp_config)
            await Engine.persist_capabilities(db, mcp.id, tools, resources, prompts)
        except MCPTransportError:
            pass
        return mcp

    # ------------------------------------------------------------------
    # Utility passthrough
    # ------------------------------------------------------------------

    determine_server_type_from_json = staticmethod(determine_server_type_from_json)

    # ------------------------------------------------------------------
    # Duplicate-detection utilities (moved from router)
    # ------------------------------------------------------------------

    @staticmethod
    async def check_duplicates(
        db: AsyncSession, config: MCPBase, *, exclude_id: str | None = None
    ) -> list[str]:
        """Return list of conflict strings for a single config."""

        conflicts: list[str] = []

        q = select(MCP)
        if exclude_id:
            q = q.where(MCP.id != exclude_id)

        # Name duplicates within same environment
        if config.name and config.name.strip():
            name_q = q.where(
                and_(MCP.name == config.name.strip(), MCP.environment == config.environment)
            )
            if (await db.execute(name_q)).scalar_one_or_none():
                conflicts.append(
                    f"MCP with name '{config.name}' already exists in environment '{config.environment}'"
                )

        # Config duplicates
        if config.server_type == ServerType.COMMAND and config.command:
            cmd_q = q.where(
                and_(
                    MCP.server_type == "command",
                    MCP.command == config.command.strip(),
                    MCP.args == config.args,
                )
            )
            if (await db.execute(cmd_q)).scalar_one_or_none():
                args_str = " ".join(config.args) if config.args else "(no args)"
                conflicts.append(
                    f"Command server with command '{config.command}' and args '{args_str}' already exists"
                )
        elif config.server_type in (ServerType.URL, ServerType.SSE) and config.url:
            url_q = q.where(
                and_(MCP.server_type.in_(["url", "sse"]), MCP.url == config.url.strip())
            )
            if (await db.execute(url_q)).scalar_one_or_none():
                conflicts.append(f"Server with URL '{config.url}' already exists")

        return conflicts

    @staticmethod
    async def bulk_check_duplicates(
        db: AsyncSession, configs: list[tuple[str, MCPBase]]
    ) -> list[str]:
        """Batch duplicate check (used by bulk import)."""

        conflicts: list[str] = []

        names_seen: set[tuple[str, str | None]] = set()
        configs_seen: set[tuple] = set()

        for name, cfg in configs:
            if cfg.name:
                key = (cfg.name.strip(), cfg.environment)
                if key in names_seen:
                    conflicts.append(
                        f"Duplicate name '{cfg.name}' found within the batch for environment '{cfg.environment}'"
                    )
                names_seen.add(key)

            if cfg.server_type == ServerType.COMMAND and cfg.command:
                cfg_key = ("command", cfg.command.strip(), tuple(cfg.args or []))
            elif cfg.server_type in (ServerType.URL, ServerType.SSE) and cfg.url:
                cfg_key = ("url", cfg.url.strip())
            else:
                cfg_key = ()

            if cfg_key and cfg_key in configs_seen:
                conflicts.append(f"Duplicate configuration found within the batch: {cfg_key}")
            if cfg_key:
                configs_seen.add(cfg_key)

        # Check against DB
        for _name, cfg in configs:
            conflicts.extend(await Engine.check_duplicates(db, cfg))

        return conflicts

    # ------------------------------------------------------------------
    # Simple DB helpers (read/delete)
    # ------------------------------------------------------------------

    @staticmethod
    async def get(db: AsyncSession, mcp_id: str) -> MCP | None:
        return (await db.execute(select(MCP).where(MCP.id == mcp_id))).scalar_one_or_none()

    @staticmethod
    async def delete(db: AsyncSession, mcp_id: str) -> None:
        await db.execute(sqldelete(MCP).where(MCP.id == mcp_id))
        await db.commit()

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        server_type: ServerType | None = None,
        environment: str | None = None,
    ) -> tuple[list[MCP], int]:
        q = select(MCP)
        if status:
            q = q.where(MCP.status == status)
        if server_type:
            q = q.where(MCP.server_type == server_type.value)
        if environment:
            q = q.where(MCP.environment == environment)

        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        rows = (
            await db.execute(q.order_by(MCP.created_at.desc()).offset(skip).limit(limit))
        ).scalars().all()

        # ------------------------------------------------------------------
        # Attach capability counts (tools/resources/prompts) to each MCP row
        # so that they are available when serialising with Pydantic models.
        # ------------------------------------------------------------------

        if rows:
            mcp_ids = [r.id for r in rows]

            # Tools count per MCP
            tool_counts_res = await db.execute(
                select(Tool.mcp_id, func.count(Tool.id)).where(Tool.mcp_id.in_(mcp_ids)).group_by(Tool.mcp_id)
            )
            tool_counts = {mcp_id: cnt for mcp_id, cnt in tool_counts_res.all()}

            # Resources count per MCP
            resource_counts_res = await db.execute(
                select(Resource.mcp_id, func.count(Resource.id)).where(Resource.mcp_id.in_(mcp_ids)).group_by(Resource.mcp_id)
            )
            resource_counts = {mcp_id: cnt for mcp_id, cnt in resource_counts_res.all()}

            # Prompts count per MCP
            prompt_counts_res = await db.execute(
                select(Prompt.mcp_id, func.count(Prompt.id)).where(Prompt.mcp_id.in_(mcp_ids)).group_by(Prompt.mcp_id)
            )
            prompt_counts = {mcp_id: cnt for mcp_id, cnt in prompt_counts_res.all()}

            # Attach dynamic attributes
            for r in rows:
                setattr(r, "tools_count", tool_counts.get(r.id, 0))
                setattr(r, "resources_count", resource_counts.get(r.id, 0))
                setattr(r, "prompts_count", prompt_counts.get(r.id, 0))

            # ----------------------------------------------------------------
            # Fetch names (lightweight) for each capability type
            # ----------------------------------------------------------------

            # Tools names
            tool_names_res = await db.execute(
                select(Tool.mcp_id, Tool.name).where(Tool.mcp_id.in_(mcp_ids))
            )
            tool_names_map: dict[str, list[str]] = {}
            for mcp_id_val, name_val in tool_names_res.all():
                tool_names_map.setdefault(mcp_id_val, []).append(name_val)

            # Resources names
            resource_names_res = await db.execute(
                select(Resource.mcp_id, Resource.name).where(Resource.mcp_id.in_(mcp_ids))
            )
            resource_names_map: dict[str, list[str]] = {}
            for mcp_id_val, name_val in resource_names_res.all():
                resource_names_map.setdefault(mcp_id_val, []).append(name_val)

            # Prompts names
            prompt_names_res = await db.execute(
                select(Prompt.mcp_id, Prompt.name).where(Prompt.mcp_id.in_(mcp_ids))
            )
            prompt_names_map: dict[str, list[str]] = {}
            for mcp_id_val, name_val in prompt_names_res.all():
                prompt_names_map.setdefault(mcp_id_val, []).append(name_val)

            for r in rows:
                setattr(r, "tool_names", tool_names_map.get(r.id, []))
                setattr(r, "resource_names", resource_names_map.get(r.id, []))
                setattr(r, "prompt_names", prompt_names_map.get(r.id, []))

        return rows, total

    @staticmethod
    async def status_summary(db: AsyncSession) -> dict:
        from datetime import datetime, timedelta, timezone
        
        status_counts = dict(
            (row.status, row.count)
            for row in (
                await db.execute(
                    select(MCP.status, func.count(MCP.id).label("count")).group_by(MCP.status)
                )
            ).all()
        )
        type_counts = dict(
            (row.server_type, row.count)
            for row in (
                await db.execute(
                    select(MCP.server_type, func.count(MCP.id).label("count")).group_by(
                        MCP.server_type
                    )
                )
            ).all()
        )
        total = (await db.execute(select(func.count(MCP.id)))).scalar()

        # Capability totals across all MCPs
        tools_total = (await db.execute(select(func.count(Tool.id)))).scalar()
        resources_total = (await db.execute(select(func.count(Resource.id)))).scalar()
        prompts_total = (await db.execute(select(func.count(Prompt.id)))).scalar()

        # Trend calculations (last 7 days vs previous 7 days)
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # Recent registrations (last 7 days)
        recent_count = (
            await db.execute(
                select(func.count(MCP.id))
                .where(MCP.created_at >= week_ago)
            )
        ).scalar()
        
        # Previous week registrations (8-14 days ago)
        previous_week_count = (
            await db.execute(
                select(func.count(MCP.id))
                .where(and_(MCP.created_at >= two_weeks_ago, MCP.created_at < week_ago))
            )
        ).scalar()
        
        # Calculate trend percentage
        if previous_week_count > 0:
            trend_percentage = ((recent_count - previous_week_count) / previous_week_count) * 100
        else:
            trend_percentage = 100.0 if recent_count > 0 else 0.0

        return {
            "total": total,
            "by_status": status_counts,
            "by_type": type_counts,
            "capabilities": {
                "tools": tools_total,
                "resources": resources_total,
                "prompts": prompts_total,
            },
            "trends": {
                "recent_registrations": recent_count,
                "previous_week_registrations": previous_week_count,
                "trend_percentage": round(trend_percentage, 1),
                "is_positive": trend_percentage >= 0,
            },
        }

    @staticmethod
    async def get_with_capabilities(db: AsyncSession, mcp_id: str) -> dict | None:
        mcp = await Engine.get(db, mcp_id)
        if not mcp:
            return None
        tools = (
            await db.execute(select(Tool).where(Tool.mcp_id == mcp_id))
        ).scalars().all()
        resources = (
            await db.execute(select(Resource).where(Resource.mcp_id == mcp_id))
        ).scalars().all()
        prompts = (
            await db.execute(select(Prompt).where(Prompt.mcp_id == mcp_id))
        ).scalars().all()

        def to_dict_list(items):
            return [itm.to_dict() for itm in items]

        return {
            **mcp.to_dict(),
            "tools": to_dict_list(tools),
            "resources": to_dict_list(resources),
            "prompts": to_dict_list(prompts),
            "tools_count": len(tools),
            "resources_count": len(resources),
            "prompts_count": len(prompts),
            "tool_names": [t.name for t in tools],
            "resource_names": [r.name for r in resources],
            "prompt_names": [p.name for p in prompts],
        }

    # ------------------------------------------------------------------
    # Validation helper (duplicates + basic field rules)
    # ------------------------------------------------------------------

    @staticmethod
    async def validate(db: AsyncSession, config: MCPBase) -> dict:
        """Return structure used by /validate endpoint."""

        conflicts = await Engine.check_duplicates(db, config)

        validation_errors: list[str] = []
        if config.server_type == ServerType.COMMAND and not config.command:
            validation_errors.append("Command is required for command-type servers")
        elif config.server_type in (ServerType.URL, ServerType.SSE) and not config.url:
            validation_errors.append("URL is required for URL/SSE-type servers")

        valid = len(conflicts) == 0 and len(validation_errors) == 0
        return {
            "valid": valid,
            "conflicts": conflicts,
            "validation_errors": validation_errors,
            "message": "Configuration is valid" if valid else "Configuration has issues",
        }

    # ------------------------------------------------------------------
    # Fleet health report  ------------------------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    async def health_report(db: AsyncSession) -> dict:  # pragma: no cover – new feature
        """Return overall health and per-MCP issues.

        An MCP is considered *healthy* when it is reachable **and** the
        capabilities returned by a live probe match what is stored in the
        database (tools / resources / prompts).
        """
        from asyncio import wait_for, TimeoutError as AsyncTimeoutError
        from datetime import datetime, timezone

        # Helper to calculate set diffs ------------------------------------------------
        def _calc_diff(live: set[str], stored: set[str]) -> dict | None:
            missing = stored - live   # expected but not reported
            extra = live - stored     # reported but unknown in DB
            return {"missing": list(missing), "extra": list(extra)} if missing or extra else None

        # Collect all MCP rows ---------------------------------------------------------
        rows = (
            await db.execute(select(MCP).order_by(MCP.created_at.desc()))
        ).scalars().all()
        total = len(rows)

        issues: list[dict] = []

        for mcp in rows:
            mcp_issue: dict[str, Any] = {
                "id": mcp.id,
                "name": mcp.name,
                "unreachable": False,
                "tool_diff": None,
                "resource_diff": None,
                "prompt_diff": None,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                # Probe with 5-second timeout to keep UI snappy.
                tools_live, resources_live, prompts_live = await wait_for(
                    Engine.test(
                        MCPBase(
                            name=mcp.name,
                            server_type=mcp.server_type,  # type: ignore[arg-type]
                            command=mcp.command,
                            args=mcp.args,
                            url=mcp.url,
                            env=mcp.env,
                            environment=mcp.environment,
                        )
                    ),
                    timeout=5.0,
                )
            except (MCPTransportError, AsyncTimeoutError):
                mcp_issue["unreachable"] = True
                issues.append(mcp_issue)
                continue

            # Build live ID sets -------------------------------------------------------
            live_tool_ids = {t.get("id") for t in tools_live if t.get("id")}
            live_res_ids = {r.get("id") for r in resources_live if r.get("id")}
            live_prompt_ids = {p.get("id") for p in prompts_live if p.get("id")}

            # Stored sets (already indexed on row via relationships) -------------------
            stored_tool_ids = {t.id for t in mcp.tools} if hasattr(mcp, "tools") else set()
            stored_res_ids = {r.id for r in mcp.resources} if hasattr(mcp, "resources") else set()
            stored_prompt_ids = {p.id for p in mcp.prompts} if hasattr(mcp, "prompts") else set()

            mcp_issue["tool_diff"] = _calc_diff(live_tool_ids, stored_tool_ids)
            mcp_issue["resource_diff"] = _calc_diff(live_res_ids, stored_res_ids)
            mcp_issue["prompt_diff"] = _calc_diff(live_prompt_ids, stored_prompt_ids)

            # Keep only MCPs with any issue
            if mcp_issue["unreachable"] or mcp_issue["tool_diff"] or mcp_issue["resource_diff"] or mcp_issue["prompt_diff"]:
                issues.append(mcp_issue)

        return {
            "is_healthy": len(issues) == 0,
            "total": total,
            "issues": issues,
        } 