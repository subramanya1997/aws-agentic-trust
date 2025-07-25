from sqlalchemy import Column, String, Text, ForeignKey, Index

from .base import Base

class Resource(Base):
    """Resource exposed by an MCP server"""

    __tablename__ = "mcp_resources"

    id = Column(String(36), primary_key=True)
    mcp_id = Column(String(36), ForeignKey("mcps.id", ondelete="CASCADE"), nullable=False, index=True)

    uri = Column(String(500), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    mime_type = Column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_resource_mcp_uri", "mcp_id", "uri", unique=True),
    ) 