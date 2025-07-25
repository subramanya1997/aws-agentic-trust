"""Entry point for running the bridge as a module.

Usage:
    python -m agentictrust.backend.bridge --transport sse --port 8100
"""

from agentictrust.backend.bridge.main import main

if __name__ == "__main__":
    main() 