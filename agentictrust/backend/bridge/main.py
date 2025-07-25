#!/usr/bin/env python3
"""CLI entry point for the Agent-Aware MCP Bridge Server.

Usage:
    python -m agentictrust.backend.bridge --transport sse --port 8100
    python -m agentictrust.backend.bridge --transport stdio
"""

import argparse
import asyncio
import logging
import sys
from typing import Literal

from agentictrust.backend.bridge.server import AgentAwareMCPBridge
from agentictrust.backend.bridge.auth_middleware import BridgeAuthMiddleware

# ----------------------------------------------------------------------
# Temporary: disable all logging output completely to ensure that the stdio
# transport never mixes logging lines with JSON-RPC messages. This can be
# revisited once a dedicated stderr-only logging solution is in place.
# ----------------------------------------------------------------------
logging.disable(logging.CRITICAL)

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the bridge server."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,  # Use stderr to avoid interfering with stdio transport
    )


async def run_bridge_server(
    transport: Literal["stdio", "sse", "streamable-http"] = "sse",
    port: int = 8100,
    host: str = "127.0.0.1",
) -> None:
    """Run the bridge server with the specified transport."""
    
    # Create bridge server
    bridge = AgentAwareMCPBridge()
    
    if transport == "stdio":
        logger.info("Starting bridge server with stdio transport")
        await bridge.run_stdio_async()
        
    elif transport == "sse":
        logger.info(f"Starting bridge server with SSE transport on {host}:{port}")
        
        # Create SSE app with authentication middleware
        sse_app = bridge.sse_app()
        
        # Note: Authentication middleware is already added in bridge.sse_app()
        
        # Run with uvicorn
        import uvicorn
        config = uvicorn.Config(
            app=sse_app,
            host=host,
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    elif transport == "streamable-http":
        logger.info(f"Starting bridge server with StreamableHTTP transport on {host}:{port}")
        
        # Create StreamableHTTP app with auth middleware
        http_app = bridge.streamable_http_app()
        
        # Add authentication middleware
        http_app.add_middleware(BridgeAuthMiddleware, bridge_server=bridge)
        
        # Run with uvicorn
        import uvicorn
        config = uvicorn.Config(
            app=http_app,
            host=host,
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    else:
        raise ValueError(f"Unsupported transport: {transport}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent-Aware MCP Bridge Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with SSE transport (default)
  python -m agentictrust.backend.bridge --transport sse --port 8100
  
  # Run with stdio transport
  python -m agentictrust.backend.bridge --transport stdio
  
  # Run with StreamableHTTP transport
  python -m agentictrust.backend.bridge --transport streamable-http --port 8200

Authentication:
  All transports require HTTP Basic authentication with agent credentials:
  - Username: agent client_id
  - Password: agent client_secret
        """,
    )
    
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="sse",
        help="Transport protocol to use (default: sse)",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8100,
        help="Port to listen on for HTTP transports (default: 8100)",
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for HTTP transports (default: 127.0.0.1)",
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    try:
        # Run the bridge server
        asyncio.run(run_bridge_server(
            transport=args.transport,
            port=args.port,
            host=args.host,
        ))
    except KeyboardInterrupt:
        logger.info("Bridge server stopped by user")
    except Exception as e:
        logger.error(f"Bridge server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 