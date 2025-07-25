"""Models for tracking agent usage of MCP capabilities"""

from sqlalchemy import Column, String, ForeignKey, Index, DateTime, Integer
from sqlalchemy.sql import func
from datetime import datetime, timezone

from .base import Base


class AgentMCPUsage(Base):
    """Track which agents are using which MCP servers"""

    __tablename__ = "agent_mcp_usage"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    mcp_id = Column(String(36), ForeignKey("mcps.id", ondelete="CASCADE"), nullable=False)
    
    # Connection tracking
    is_connected = Column(String(10), default="false", nullable=False)  # "true" or "false"
    connected_at = Column(DateTime(timezone=True), nullable=True)
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage statistics
    total_tool_calls = Column(Integer, default=0, nullable=False)
    total_resource_reads = Column(Integer, default=0, nullable=False)
    total_prompt_gets = Column(Integer, default=0, nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_agent_mcp_usage_agent", "agent_id"),
        Index("idx_agent_mcp_usage_mcp", "mcp_id"),
        Index("idx_agent_mcp_usage_connected", "is_connected"),
        Index("idx_agent_mcp_usage_unique", "agent_id", "mcp_id", unique=True),
    )

    def connect(self) -> None:
        """Mark agent as connected to this MCP"""
        self.is_connected = "true"
        self.connected_at = datetime.now(timezone.utc)
        self.last_activity_at = datetime.now(timezone.utc)

    def disconnect(self) -> None:
        """Mark agent as disconnected from this MCP"""
        self.is_connected = "false"
        self.disconnected_at = datetime.now(timezone.utc)

    def record_tool_call(self) -> None:
        """Record a tool call"""
        if self.total_tool_calls is None:
            self.total_tool_calls = 0
        self.total_tool_calls += 1
        self.last_activity_at = datetime.now(timezone.utc)

    def record_resource_read(self) -> None:
        """Record a resource read"""
        if self.total_resource_reads is None:
            self.total_resource_reads = 0
        self.total_resource_reads += 1
        self.last_activity_at = datetime.now(timezone.utc)

    def record_prompt_get(self) -> None:
        """Record a prompt get"""
        if self.total_prompt_gets is None:
            self.total_prompt_gets = 0
        self.total_prompt_gets += 1
        self.last_activity_at = datetime.now(timezone.utc)


class AgentToolUsage(Base):
    """Track which agents are using which specific tools"""

    __tablename__ = "agent_tool_usage"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(String(36), ForeignKey("mcp_tools.id", ondelete="CASCADE"), nullable=False)
    
    # Usage statistics
    total_calls = Column(Integer, default=0, nullable=False)
    last_called_at = Column(DateTime(timezone=True), nullable=True)
    first_called_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_agent_tool_usage_agent", "agent_id"),
        Index("idx_agent_tool_usage_tool", "tool_id"),
        Index("idx_agent_tool_usage_unique", "agent_id", "tool_id", unique=True),
    )

    def record_call(self) -> None:
        """Record a tool call"""
        if self.total_calls is None:
            self.total_calls = 0
        self.total_calls += 1
        self.last_called_at = datetime.now(timezone.utc)
        if self.first_called_at is None:
            self.first_called_at = datetime.now(timezone.utc)


class AgentResourceUsage(Base):
    """Track which agents are using which specific resources"""

    __tablename__ = "agent_resource_usage"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(String(36), ForeignKey("mcp_resources.id", ondelete="CASCADE"), nullable=False)
    
    # Usage statistics
    total_reads = Column(Integer, default=0, nullable=False)
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    first_read_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_agent_resource_usage_agent", "agent_id"),
        Index("idx_agent_resource_usage_resource", "resource_id"),
        Index("idx_agent_resource_usage_unique", "agent_id", "resource_id", unique=True),
    )

    def record_read(self) -> None:
        """Record a resource read"""
        if self.total_reads is None:
            self.total_reads = 0
        self.total_reads += 1
        self.last_read_at = datetime.now(timezone.utc)
        if self.first_read_at is None:
            self.first_read_at = datetime.now(timezone.utc)


class AgentPromptUsage(Base):
    """Track which agents are using which specific prompts"""

    __tablename__ = "agent_prompt_usage"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    prompt_id = Column(String(36), ForeignKey("mcp_prompts.id", ondelete="CASCADE"), nullable=False)
    
    # Usage statistics
    total_gets = Column(Integer, default=0, nullable=False)
    last_got_at = Column(DateTime(timezone=True), nullable=True)
    first_got_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_agent_prompt_usage_agent", "agent_id"),
        Index("idx_agent_prompt_usage_prompt", "prompt_id"),
        Index("idx_agent_prompt_usage_unique", "agent_id", "prompt_id", unique=True),
    )

    def record_get(self) -> None:
        """Record a prompt get"""
        if self.total_gets is None:
            self.total_gets = 0
        self.total_gets += 1
        self.last_got_at = datetime.now(timezone.utc)
        if self.first_got_at is None:
            self.first_got_at = datetime.now(timezone.utc) 