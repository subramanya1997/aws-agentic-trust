from sqlalchemy import Column, String, Text, ForeignKey, Index

from .base import Base
from .mcp import JSONDict, JSONList

class Prompt(Base):
    """Prompt template exposed by an MCP server"""

    __tablename__ = "mcp_prompts"

    id = Column(String(36), primary_key=True)
    mcp_id = Column(String(36), ForeignKey("mcps.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    arguments = Column(JSONList, nullable=False, default=list)

    __table_args__ = (
        Index("idx_prompt_mcp_name", "mcp_id", "name", unique=True),
    ) 