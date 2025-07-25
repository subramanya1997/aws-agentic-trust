"""MCP server model (replaces the old Upstream model)"""

import json
from typing import List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Index, Integer, DateTime
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.sql import func

from .base import Base


class JSONList(TypeDecorator):
    """Custom type for storing list as JSON string"""
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class JSONDict(TypeDecorator):
    """Custom type for storing dict as JSON string"""
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class MCP(Base):
    """Model representing an MCP server instance"""

    __tablename__ = "mcps"

    # Primary key
    id = Column(String(36), primary_key=True)

    # Server type: command, url, sse
    server_type = Column(String(20), nullable=False, default="command")

    # Command-based configuration
    command = Column(String(500), nullable=True)
    args = Column(JSONList, nullable=False, default=list)

    # URL-based configuration
    url = Column(String(1000), nullable=True)

    # Environment variables
    env = Column(JSONDict, nullable=False, default=dict)

    # Metadata
    name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Status / health
    status = Column(String(20), default="registered")
    health_check_url = Column(String(500), nullable=True)
    last_health_check = Column(String(50), nullable=True)

    # Connection tracking
    connected_instances = Column(Integer, default=0, nullable=False)
    last_connected_at = Column(DateTime(timezone=True), nullable=True)
    last_disconnected_at = Column(DateTime(timezone=True), nullable=True)
    total_connections = Column(Integer, default=0, nullable=False)

    # Misc
    environment = Column(String(50), default="development")
    config = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_mcps_status", "status"),
        Index("idx_mcps_environment", "environment"),
        Index("idx_mcps_server_type", "server_type"),
        Index("idx_mcps_created_at", "created_at"),
        Index("idx_mcps_connected_instances", "connected_instances"),
    )

    # Helper properties -------------------------------------------------

    @property
    def args_list(self) -> List[str]:
        return self.args if self.args is not None else []

    @args_list.setter
    def args_list(self, value: List[str]) -> None:
        self.args = value

    @property
    def env_dict(self) -> Dict[str, Any]:
        return self.env if self.env is not None else {}

    @env_dict.setter
    def env_dict(self, value: Dict[str, Any]) -> None:
        self.env = value

    # Helpers -----------------------------------------------------------

    def is_active(self) -> bool:
        return self.status == "active"

    def is_connected(self) -> bool:
        return self.connected_instances > 0

    def validate_configuration(self) -> bool:
        if self.server_type == "command":
            return bool(self.command and self.command.strip())
        if self.server_type in ("url", "sse"):
            return bool(self.url and self.url.strip())
        return False

    def increment_connection(self) -> None:
        """Increment connection count and update timestamps"""
        self.connected_instances += 1
        self.total_connections += 1
        self.last_connected_at = datetime.now(timezone.utc)
        if self.status != "active":
            self.status = "active"

    def decrement_connection(self) -> None:
        """Decrement connection count and update timestamps"""
        if self.connected_instances > 0:
            self.connected_instances -= 1
        self.last_disconnected_at = datetime.now(timezone.utc)
        if self.connected_instances == 0 and self.status == "active":
            self.status = "registered"

    # -------------------------------------------------------------------
    def __repr__(self) -> str:
        details = self.command if self.server_type == "command" else self.url
        return (
            f"<MCP(id='{self.id}', type='{self.server_type}', "
            f"details='{details}', status='{self.status}', "
            f"instances={self.connected_instances})>"
        ) 