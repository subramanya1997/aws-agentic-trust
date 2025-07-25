from pydantic import BaseModel, Field, validator
from typing import Optional

class CapabilityItem(BaseModel):
    id: str = Field(...)
    name: str = Field(...)
    mcp_id: Optional[str] = None
    mcp_name: Optional[str] = None

class CapabilityListResponse(BaseModel):
    items: list[CapabilityItem] 