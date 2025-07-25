"""Pydantic schemas for log entry validation"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator


class LogEntryBase(BaseModel):
    """Base schema for log entries"""
    
    timestamp: str = Field(..., description="ISO timestamp of the event")
    event_type: str = Field(..., description="Type of event", max_length=100)
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data as JSON")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking related events")
    session_id: Optional[str] = Field(None, description="Session ID for grouping events")
    source: Optional[str] = Field(None, description="Source service or component", max_length=100)
    severity: str = Field(default="info", description="Log severity level")
    
    @validator("event_type")
    def validate_event_type(cls, v):
        if not v or not v.strip():
            raise ValueError("Event type cannot be empty")
        return v.strip()
    
    @validator("severity")
    def validate_severity(cls, v):
        allowed_severities = ["debug", "info", "warning", "error", "critical"]
        if v not in allowed_severities:
            raise ValueError(f"Severity must be one of: {', '.join(allowed_severities)}")
        return v


class LogEntryCreate(LogEntryBase):
    """Schema for creating a new log entry"""
    pass


class LogEntryResponse(LogEntryBase):
    """Schema for log entry responses"""
    
    id: int = Field(..., description="Unique identifier for the log entry")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LogEntryListResponse(BaseModel):
    """Schema for paginated log entry list responses"""
    
    items: List[LogEntryResponse]
    total: int = Field(..., description="Total number of log entries")
    page: int = Field(default=1, description="Current page number")
    size: int = Field(default=100, description="Number of items per page")
    
    class Config:
        from_attributes = True


# Legacy schemas for backward compatibility
class LegacyLogEntry(BaseModel):
    """Legacy log entry schema for backward compatibility"""
    
    id: Optional[int] = None
    timestamp: str
    event_type: str
    data: Dict[str, Any]
    
    class Config:
        from_attributes = True


class LogBatchRequest(BaseModel):
    """Schema for batch log ingestion"""
    
    logs: List[LogEntryCreate] = Field(..., description="List of log entries to ingest")
    
    @validator("logs")
    def validate_logs_not_empty(cls, v):
        if not v:
            raise ValueError("Logs list cannot be empty")
        if len(v) > 1000:
            raise ValueError("Cannot ingest more than 1000 logs at once")
        return v 