"""Observability models for events and analytics"""

import json
from typing import Any, Dict

from sqlalchemy import Column, Integer, String, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
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


class EventEntry(Base):
    """Model for raw JSON-RPC event messages (for resumability)"""
    
    __tablename__ = "events"
    
    # Event identification
    event_id = Column(String(36), primary_key=True)
    stream_id = Column(String(36), nullable=False)
    
    # Event timing and metadata
    timestamp = Column(String(50), nullable=False)
    message_type = Column(String(50), nullable=False)
    method = Column(String(100), nullable=True)
    
    # Event content
    message_data = Column(Text, nullable=False)  # Complete JSON-RPC message
    
    # Processing status
    synced = Column(Boolean, default=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_events_stream_timestamp", "stream_id", "timestamp"),
        Index("idx_events_synced", "synced"),
        Index("idx_events_method", "method"),
        Index("idx_events_created_at", "created_at"),
    )
    
    @property
    def message_dict(self) -> Dict[str, Any]:
        """Get message data as dictionary"""
        if self.message_data:
            return json.loads(self.message_data)
        return {}
    
    @message_dict.setter
    def message_dict(self, value: Dict[str, Any]) -> None:
        """Set message data from dictionary"""
        self.message_data = json.dumps(value)
    
    def mark_synced(self) -> None:
        """Mark event as synced"""
        self.synced = True
    
    def __repr__(self) -> str:
        return f"<EventEntry(event_id='{self.event_id}', method='{self.method}', synced={self.synced})>"


class ObservabilityEntry(Base):
    """Model for processed observability insights"""
    
    __tablename__ = "observability"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Optional reference to source event
    event_id = Column(String(36), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=True)
    
    # Event timing and classification
    timestamp = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    
    # Processed insights (JSON)
    data = Column(JSONData, nullable=False, default=dict)
    
    # Processing status
    synced = Column(Boolean, default=False)
    
    # Relationships
    source_event = relationship("EventEntry", backref="observability_entries")
    
    # Indexes
    __table_args__ = (
        Index("idx_observability_synced", "synced"),
        Index("idx_observability_type", "event_type"),
        Index("idx_observability_timestamp", "timestamp"),
        Index("idx_observability_event_id", "event_id"),
        Index("idx_observability_created_at", "created_at"),
    )
    
    @property
    def data_dict(self) -> Dict[str, Any]:
        """Get data as dictionary"""
        return self.data if self.data is not None else {}
    
    @data_dict.setter
    def data_dict(self, value: Dict[str, Any]) -> None:
        """Set data from dictionary"""
        self.data = value
    
    def mark_synced(self) -> None:
        """Mark entry as synced"""
        self.synced = True
    
    def __repr__(self) -> str:
        return f"<ObservabilityEntry(id={self.id}, event_type='{self.event_type}', synced={self.synced})>" 