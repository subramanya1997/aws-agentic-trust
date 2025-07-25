"""AgenticTrust Data Layer

Modern SQLAlchemy-based data layer with support for both SQLite (development) 
and PostgreSQL (production) databases.
"""

# Import models for easy access
from .models.base import Base
from .models.mcp import MCP
from .models.logs import LogEntry
from .models.observability import ObservabilityEntry, EventEntry

# Import paths (keeping for backward compatibility)
from .paths import get_db_path, DATA_ROOT

# Legacy SQLite support (for migration compatibility)
from .sqlite import get_connection as get_legacy_connection

__all__ = [
    # Models
    "Base",
    "MCP",
    "LogEntry", 
    "ObservabilityEntry",
    "EventEntry",
    
    # Paths
    "get_db_path",
    "DATA_ROOT",
    
    # Legacy support
    "get_legacy_connection",
] 