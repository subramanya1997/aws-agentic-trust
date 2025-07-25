"""Log entry model for system event logging"""

import json
from typing import Any, Dict

from sqlalchemy import Column, Integer, String, Text, Index
from sqlalchemy.types import TypeDecorator, VARCHAR

from .base import Base


class JSONData(TypeDecorator):
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


class LogEntry(Base):
    """Model for system event logs"""
    
    __tablename__ = "logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event information
    timestamp = Column(String(50), nullable=False)  # ISO timestamp
    event_type = Column(String(100), nullable=False)
    
    # Event data (JSON)
    data = Column(JSONData, nullable=False, default=dict)
    
    # Optional correlation tracking
    correlation_id = Column(String(36), nullable=True)
    session_id = Column(String(36), nullable=True)
    
    # Event metadata
    source = Column(String(100), nullable=True)  # source service/component
    severity = Column(String(20), default="info")  # debug, info, warning, error, critical
    
    # Indexes
    __table_args__ = (
        Index("idx_logs_timestamp", "timestamp"),
        Index("idx_logs_event_type", "event_type"),
        Index("idx_logs_correlation_id", "correlation_id"),
        Index("idx_logs_severity", "severity"),
        Index("idx_logs_created_at", "created_at"),
    )
    
    @property
    def data_dict(self) -> Dict[str, Any]:
        """Get data as a dictionary"""
        return self.data if self.data is not None else {}
    
    @data_dict.setter 
    def data_dict(self, value: Dict[str, Any]) -> None:
        """Set data from a dictionary"""
        self.data = value
    
    def is_error(self) -> bool:
        """Check if this is an error log entry"""
        return self.severity in ("error", "critical")
    
    def __repr__(self) -> str:
        return f"<LogEntry(id={self.id}, event_type='{self.event_type}', severity='{self.severity}')>" 