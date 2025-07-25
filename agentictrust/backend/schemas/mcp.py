"""Pydantic schemas for MCP servers (replaces Upstream)"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator


class ServerType(str, Enum):
    COMMAND = "command"
    URL = "url"
    SSE = "sse"


class MCPBase(BaseModel):
    """Base schema for MCP servers"""

    server_type: ServerType = Field(default=ServerType.COMMAND)

    # Command-based
    command: Optional[str] = Field(None, max_length=500)
    args: List[str] = Field(default_factory=list)

    # URL-based
    url: Optional[str] = Field(None, max_length=1000)

    # Env vars
    env: Dict[str, str] = Field(default_factory=dict)

    # Meta
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    environment: str = Field(default="development")
    config: Optional[Dict[str, Any]] = None

    # Validators --------------------------------------------------------

    @validator("command")
    def _cmd_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("command cannot be blank")
        return v.strip() if v else v

    @validator("url")
    def _url_valid(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("url cannot be blank")
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("url must start with http:// or https://")
        return v

    @root_validator(skip_on_failure=True)
    def _type_specific_rules(cls, values):
        st = values.get("server_type")
        cmd = values.get("command")
        url = values.get("url")
        if st == ServerType.COMMAND and not cmd:
            raise ValueError("command-based servers require 'command'")
        if st in (ServerType.URL, ServerType.SSE) and not url:
            raise ValueError("url-based servers require 'url'")
        return values


class MCPUpdate(BaseModel):
    server_type: Optional[ServerType] = None
    command: Optional[str] = Field(None, max_length=500)
    args: Optional[List[str]] = None
    url: Optional[str] = Field(None, max_length=1000)
    env: Optional[Dict[str, str]] = None
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None)
    environment: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    id: str
    server_type: ServerType
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    env: Dict[str, str] = Field(default_factory=dict)
    name: Optional[str] = None
    description: Optional[str] = None
    status: str
    health_check_url: Optional[str] = None
    last_health_check: Optional[str] = None
    environment: str
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    # Capability counts (populated dynamically)
    tools_count: int = 0
    resources_count: int = 0
    prompts_count: int = 0
    # Names (optional lightweight capabilities for list view)
    tool_names: List[str] = Field(default_factory=list)
    resource_names: List[str] = Field(default_factory=list)
    prompt_names: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class MCPListResponse(BaseModel):
    items: List[MCPResponse]
    total: int
    page: int = 1
    size: int = 50

    class Config:
        from_attributes = True


# Bulk JSON config ------------------------------------

class MCPServerConfig(BaseModel):
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None

    @root_validator(skip_on_failure=True)
    def _one_of(cls, values):
        if not values.get("command") and not values.get("url"):
            raise ValueError("Either command or url must be provided")
        if values.get("command") and values.get("url"):
            raise ValueError("Provide either command or url, not both")
        return values


class MCPServersConfig(BaseModel):
    mcpServers: Dict[str, MCPServerConfig] 


# ---------------------------------------------------------------------------
# Capability schemas (tools/resources/prompts) used by test & view endpoints
# ---------------------------------------------------------------------------

class MCPTestResult(BaseModel):
    """Schema returned when testing connectivity to an MCP server before registration.

    It is also reused for the detailed view endpoint.
    """

    tools: List[Dict[str, Any]] = Field(default_factory=list)
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    prompts: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Detailed MCP view schema (extends base response with capabilities)
# ---------------------------------------------------------------------------

class MCPDetailedResponse(MCPResponse):
    """Full MCP detail including persisted tools/resources/prompts."""

    tools: List[Dict[str, Any]] = Field(default_factory=list)
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    prompts: List[Dict[str, Any]] = Field(default_factory=list) 