from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agentictrust.backend.api.dependencies import DatabaseSession
from agentictrust.backend.data.models.tool import Tool
from agentictrust.backend.data.models.resource import Resource
from agentictrust.backend.data.models.prompt import Prompt
from agentictrust.backend.data.models.mcp import MCP
from agentictrust.backend.schemas.capabilities import CapabilityItem, CapabilityListResponse

router = APIRouter()


def _attach_mcp_names(rows, db_map):
    items = []
    for r in rows:
        items.append(
            CapabilityItem(
                id=r.id,
                name=r.name,
                mcp_id=r.mcp_id,
                mcp_name=db_map.get(r.mcp_id),
            )
        )
    return CapabilityListResponse(items=items)


async def _build_mcp_name_map(db: AsyncSession, mcp_ids: set[str]):
    if not mcp_ids:
        return {}
    res = await db.execute(select(MCP.id, MCP.name).where(MCP.id.in_(mcp_ids)))
    return {row.id: row.name for row in res}


@router.get("/tools", response_model=CapabilityListResponse, summary="List all tools across MCPs")
async def list_tools(db: AsyncSession = DatabaseSession):
    rows = (await db.execute(select(Tool.id, Tool.name, Tool.mcp_id))).all()
    mcp_map = await _build_mcp_name_map(db, {r.mcp_id for r in rows if r.mcp_id})
    return _attach_mcp_names(rows, mcp_map)


@router.get("/resources", response_model=CapabilityListResponse, summary="List all resources across MCPs")
async def list_resources(db: AsyncSession = DatabaseSession):
    rows = (await db.execute(select(Resource.id, Resource.name, Resource.mcp_id))).all()
    mcp_map = await _build_mcp_name_map(db, {r.mcp_id for r in rows if r.mcp_id})
    return _attach_mcp_names(rows, mcp_map)


@router.get("/prompts", response_model=CapabilityListResponse, summary="List all prompts across MCPs")
async def list_prompts(db: AsyncSession = DatabaseSession):
    rows = (await db.execute(select(Prompt.id, Prompt.name, Prompt.mcp_id))).all()
    mcp_map = await _build_mcp_name_map(db, {r.mcp_id for r in rows if r.mcp_id})
    return _attach_mcp_names(rows, mcp_map) 