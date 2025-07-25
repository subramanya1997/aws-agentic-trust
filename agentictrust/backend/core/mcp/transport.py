from __future__ import annotations

import logging
from datetime import timedelta
from typing import List, Dict, Any, Tuple, AsyncContextManager, Callable, Awaitable

from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.types import Tool, Resource, Prompt  # noqa: F401

from agentictrust.backend.schemas.mcp import MCPBase, ServerType

logger = logging.getLogger(__name__)


class MCPTransportError(Exception):
    """Raised when connectivity or introspection of an MCP server fails."""


# ---------------------------------------------------------------------------
# Helper to attach a cleanup coroutine (e.g., env reset) to an async
# context-manager that we don't control.
# ---------------------------------------------------------------------------

def _wrap_cm_with_env_reset(cm: AsyncContextManager, cleanup_coro_factory: Callable[[], Awaitable[None]]):
    """Return a new async context manager that yields the same as *cm* but
    runs *cleanup_coro_factory*() after the inner cm exits (success or error).
    """

    class _Wrapper:  # noqa: D401
        async def __aenter__(self):
            self._inner = cm  # type: ignore[attr-defined]
            return await self._inner.__aenter__()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            try:
                return await self._inner.__aexit__(exc_type, exc_val, exc_tb)
            finally:
                await cleanup_coro_factory()

    return _Wrapper()


async def _serialise_items(items: List[Any]) -> List[Dict[str, Any]]:  # type: ignore[valid-type]
    """Convert Pydantic models to plain dicts filtered for JSON return."""
    serialised: List[Dict[str, Any]] = []
    for item in items:
        try:
            serialised.append(item.model_dump(by_alias=True, mode="json", exclude_none=True))
        except Exception:
            serialised.append(item)  # type: ignore[arg-type]
    return serialised


async def test_mcp_connection(
    config: MCPBase, timeout: int = 30
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Connect to the given MCP configuration and retrieve lists.

    Returns (tools, resources, prompts) as lists of JSON-serialisable dicts.
    """

    # ------------------------------------------------------------------
    # COMMAND-based servers – experimental support for **npx** smithery.ai
    # ------------------------------------------------------------------
    if config.server_type == ServerType.COMMAND:
        # We only support the special NPX invocation used by smithery.ai for now.
        # Example:  command="npx"  args=["-y", "@smithery/cli@latest", "install", "@Dhravya/apple-mcp"]

        cmd = (config.command or "").strip()
        if cmd != "npx":
            raise MCPTransportError(
                "Testing generic command-type MCP servers is not supported – only NPX smithery.ai CLI is allowed"
            )

        # Ensure the smithery CLI package is part of the argument list
        if not any("@smithery/cli" in arg for arg in (config.args or [])):
            raise MCPTransportError(
                "Only NPX commands installing smithery.ai MCPs are supported"
            )

        try:
            # Lazily import here – not all deployments will have stdio_client available
            from mcp.client.stdio import stdio_client  # type: ignore
        except ModuleNotFoundError as exc:
            raise MCPTransportError(
                "mcp.client.stdio is required for NPX-based MCP testing but is not available"
            ) from exc

        # stdio_client signature: stdio_client(cmd: str, *args, timeout: int | None = None, cwd: str | None = None)
        # We propagate custom env vars by temporarily updating os.environ inside the context manager below.
        from mcp.client.stdio import StdioServerParameters  # type: ignore

        # Build StdioServerParameters
        server_params = StdioServerParameters(
            command=cmd,
            args=list(config.args or []),
            env=config.env if config.env else None,
        )

        client_cm_base = stdio_client(server_params)  # type: ignore[arg-type]

        async def _restore_env():
            # No environment mutation needed since we pass env directly to the child process
            return None

        client_cm = _wrap_cm_with_env_reset(client_cm_base, _restore_env)

    else:
        if not config.url:
            raise MCPTransportError("'url' must be provided for URL / SSE server types")

        url = config.url.strip()

        if config.server_type == ServerType.SSE:
            client_cm = sse_client(url, timeout=5)
        else:
            client_cm = streamablehttp_client(url, timeout=timedelta(seconds=timeout))

    try:
        async with client_cm as ctx:
            if isinstance(ctx, tuple) and len(ctx) == 3:
                read_stream, write_stream, _ = ctx  # type: ignore[misc]
            else:
                read_stream, write_stream = ctx  # type: ignore[misc]

            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                tools: List[Dict[str, Any]] = []
                resources: List[Dict[str, Any]] = []
                prompts: List[Dict[str, Any]] = []

                try:
                    t_res = await session.list_tools()
                    tools = await _serialise_items(t_res.tools)
                except Exception as exc:
                    logger.warning("Could not retrieve tools list: %s", exc)

                try:
                    p_res = await session.list_prompts()
                    prompts = await _serialise_items(p_res.prompts)
                except Exception as exc:
                    logger.warning("Could not retrieve prompts list: %s", exc)

                try:
                    r_res = await session.list_resources()
                    resources = await _serialise_items(r_res.resources)
                except Exception as exc:
                    logger.warning("Could not retrieve resources list: %s", exc)

                return tools, resources, prompts
    except Exception as exc:
        # Identify the target for logging purposes
        target_id = (
            url if "url" in locals() else f"command: {cmd} {' '.join(config.args or [])}"
        )
        logger.error("Failed to connect to MCP server %s: %s", target_id, exc)
        raise MCPTransportError(str(exc)) from exc 