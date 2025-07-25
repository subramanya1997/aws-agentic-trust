"""Standard response schemas for common API responses"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """Standard success response schema"""
    
    status: str = Field(default="success", description="Response status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    
    error: Dict[str, Any] = Field(..., description="Error details")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "type": "ValidationError",
                    "message": "Invalid input data",
                    "details": {},
                    "correlation_id": "uuid-string"
                }
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response schema"""
    
    status: str = Field(..., description="Service health status")
    database: str = Field(..., description="Database connection string")
    schema_version: Optional[int] = Field(None, description="Current database schema version")
    tables_accessible: bool = Field(..., description="Whether database tables are accessible")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")


class InfoResponse(BaseModel):
    """System information response schema"""
    
    database_path: str = Field(..., description="Path to database file")
    statistics: Dict[str, Any] = Field(..., description="System statistics")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Current environment")
    features: Dict[str, bool] = Field(default_factory=dict, description="Enabled features")


class DeleteResponse(BaseModel):
    """Standard delete operation response"""
    
    status: str = Field(default="deleted", description="Deletion status")
    id: str = Field(..., description="ID of the deleted resource")
    message: Optional[str] = Field(None, description="Optional deletion message") 