"""Centralized path management for AgenticTrust data storage.

This module defines where database files and other persistent data are stored,
ensuring consistency across proxy and backend services.
"""

import os
from pathlib import Path

# Default data root - can be overridden via environment variable
DATA_ROOT = Path(os.environ.get("AGENTICTRUST_DATA_ROOT", Path.home() / ".agentictrust"))

# Ensure data directories exist
DATA_ROOT.mkdir(parents=True, exist_ok=True)
(DATA_ROOT / "db").mkdir(parents=True, exist_ok=True)


def get_db_path(name: str = "agentictrust.db") -> Path:
    """Get the path to a database file.
    
    Args:
        name: Database filename (defaults to main agentictrust.db)
        
    Returns:
        Full path to the database file
    """
    return DATA_ROOT / "db" / name


def get_backup_path() -> Path:
    """Get the path for database backups."""
    backup_dir = DATA_ROOT / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_logs_path() -> Path:
    """Get the path for log files."""
    logs_dir = DATA_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir 