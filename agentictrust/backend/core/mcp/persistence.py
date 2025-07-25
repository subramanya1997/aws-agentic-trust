import uuid
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from agentictrust.backend.data.models.tool import Tool
from agentictrust.backend.data.models.resource import Resource
from agentictrust.backend.data.models.prompt import Prompt


async def persist_capabilities(
    db: AsyncSession,
    mcp_id: str,
    tools: List[Dict[str, Any]],
    resources: List[Dict[str, Any]],
    prompts: List[Dict[str, Any]],
) -> None:
    """Persist tools, resources and prompts for the given MCP.

    Strategy: delete existing rows for this MCP and insert fresh ones.
    """

    # Wipe existing
    await db.execute(delete(Tool).where(Tool.mcp_id == mcp_id))
    await db.execute(delete(Resource).where(Resource.mcp_id == mcp_id))
    await db.execute(delete(Prompt).where(Prompt.mcp_id == mcp_id))

    # Insert new ones
    for t in tools:
        db.add(
            Tool(
                id=str(uuid.uuid4()),
                mcp_id=mcp_id,
                name=t.get("name"),
                description=t.get("description"),
                input_schema=t.get("inputSchema") or {},
            )
        )
    for r in resources:
        db.add(
            Resource(
                id=str(uuid.uuid4()),
                mcp_id=mcp_id,
                uri=r.get("uri"),
                name=r.get("name"),
                description=r.get("description"),
                mime_type=r.get("mimeType"),
            )
        )
    for p in prompts:
        db.add(
            Prompt(
                id=str(uuid.uuid4()),
                mcp_id=mcp_id,
                name=p.get("name"),
                description=p.get("description"),
                arguments=p.get("arguments") or [],
            )
        )

    await db.commit() 