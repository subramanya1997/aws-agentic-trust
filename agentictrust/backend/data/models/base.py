"""Base SQLAlchemy model with common functionality"""

from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr


class BaseModel:
    """Base model with common columns and functionality"""
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # Common timestamp columns
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                # Ensure all timestamps are explicitly marked as UTC
                if value.tzinfo is None:
                    # If naive datetime, assume it's UTC and make it timezone-aware
                    value = value.replace(tzinfo=timezone.utc)
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """String representation of the model"""
        class_name = self.__class__.__name__
        attrs = []
        
        # Add primary key if exists
        if hasattr(self, 'id'):
            attrs.append(f"id={getattr(self, 'id')}")
        
        # Add a few other meaningful attributes
        for attr in ['name', 'command', 'event_type']:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if value:
                    attrs.append(f"{attr}='{value}'")
                break
        
        attrs_str = ", ".join(attrs)
        return f"<{class_name}({attrs_str})>"


# Create the declarative base
Base = declarative_base(cls=BaseModel) 