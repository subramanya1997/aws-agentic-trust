from sqlalchemy import Column, String, Text, ForeignKey, Index

from .base import Base
from .mcp import JSONDict  # reuse custom JSON type

class Tool(Base):
    """Tool exposed by an MCP server"""

    __tablename__ = "mcp_tools"

    id = Column(String(36), primary_key=True)
    mcp_id = Column(String(36), ForeignKey("mcps.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    input_schema = Column(JSONDict, nullable=False)

    __table_args__ = (
        Index("idx_tool_mcp_name", "mcp_id", "name", unique=True),
    ) 