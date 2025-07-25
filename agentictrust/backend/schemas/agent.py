from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class AgentCreate(BaseModel):
    """Payload required to register a new agent.

    Client credentials are **generated** server-side; the caller only provides
    metadata and capability scoping (list of IDs the agent may access).
    """

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None

    tool_ids: List[str] = Field(default_factory=list, description="Tool IDs the agent can invoke")
    resource_ids: List[str] = Field(default_factory=list, description="Resource IDs accessible by the agent")
    prompt_ids: List[str] = Field(default_factory=list, description="Prompt IDs accessible by the agent")


class AgentCredentials(BaseModel):
    """Returned **once** at registration; contains the plaintext secret."""

    client_id: str
    client_secret: str


class CapabilityMeta(BaseModel):
    id: str
    mcp_id: Optional[str] = None
    mcp_name: Optional[str] = None
    name: Optional[str] = None


class AgentResponse(BaseModel):
    """Full agent info (does **not** include secret)."""

    id: str
    client_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    tool_ids: List[str] = Field(default_factory=list, alias="allowed_tool_ids")
    resource_ids: List[str] = Field(default_factory=list, alias="allowed_resource_ids")
    prompt_ids: List[str] = Field(default_factory=list, alias="allowed_prompt_ids")
    created_at: datetime
    updated_at: datetime

    # Optional detailed objects
    tools: List[CapabilityMeta] = Field(default_factory=list)
    resources: List[CapabilityMeta] = Field(default_factory=list)
    prompts: List[CapabilityMeta] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True

    # Validators to normalise None → []
    @validator("tool_ids", "resource_ids", "prompt_ids", "tools", "resources", "prompts", pre=True, always=True)
    def _default_list(cls, v):
        return v or []


class AgentRegistrationResponse(BaseModel):
    """Response returned by the create endpoint: agent info + credentials."""

    agent: AgentResponse
    credentials: AgentCredentials


# Paginated list response ----------------------------------------------------


class AgentListResponse(BaseModel):
    """Standard paginated list wrapper for agents."""

    items: List[AgentResponse]
    total: int
    page: int = 1
    size: int = 50

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Update payload
# ---------------------------------------------------------------------------

class AgentUpdate(BaseModel):
    """Payload for updating an existing agent.

    All fields are optional; only the ones provided will be updated.  Capability
    lists fully replace the previous values when supplied.
    """

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None

    # When provided, these lists REPLACE the existing allowed_* lists.
    tool_ids: Optional[List[str]] = Field(None, description="Full list of tool IDs allowed after update")
    resource_ids: Optional[List[str]] = Field(None, description="Full list of resource IDs allowed after update")
    prompt_ids: Optional[List[str]] = Field(None, description="Full list of prompt IDs allowed after update")

    class Config:
        from_attributes = True 