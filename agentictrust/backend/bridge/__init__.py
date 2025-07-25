"""Agent-aware MCP Bridge Server

This package provides a multi-tenant MCP server that filters capabilities
based on authenticated agent credentials.
"""

from .server import AgentAwareMCPBridge

__all__ = ["AgentAwareMCPBridge"] 