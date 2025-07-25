"""Shared SQLite connection management for AgenticTrust.

This module provides thread-safe database connections and ensures
schema consistency across all components.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Dict, Optional

from .paths import get_db_path

# Thread-safe connection pool
_connections: Dict[str, sqlite3.Connection] = {}
_lock = threading.Lock()


def get_connection(db_name: str = "agentictrust.db") -> sqlite3.Connection:
    """Get a thread-safe SQLite connection.
    
    Args:
        db_name: Database filename (e.g., 'agentictrust.db', 'proxy.db')
        
    Returns:
        SQLite connection with row factory enabled
    """
    with _lock:
        if db_name not in _connections:
            db_path = get_db_path(db_name)
            conn = sqlite3.connect(str(db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            # Optimize for write performance
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.commit()
            
            _connections[db_name] = conn
            
            # Ensure schema is up to date
            ensure_schema(conn)
            
        return _connections[db_name]


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure the database schema is up to date.
    
    Args:
        conn: SQLite connection to apply schema to
    """
    # Read schema from the schema.sql file
    schema_path = Path(__file__).parent / "schema.sql"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    schema_sql = schema_path.read_text()
    
    # Execute the schema (uses CREATE TABLE IF NOT EXISTS, so it's safe)
    conn.executescript(schema_sql)
    conn.commit()


def get_schema_version(conn: sqlite3.Connection) -> Optional[int]:
    """Get the current schema version.
    
    Args:
        conn: SQLite connection
        
    Returns:
        Latest schema version number, or None if not found
    """
    try:
        cursor = conn.execute("SELECT MAX(version) FROM schema_versions")
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None
    except sqlite3.Error:
        return None


def close_connection(db_name: str = "agentictrust.db") -> None:
    """Close a specific database connection.
    
    Args:
        db_name: Database filename to close
    """
    with _lock:
        if db_name in _connections:
            _connections[db_name].close()
            del _connections[db_name]


def close_all_connections() -> None:
    """Close all database connections."""
    with _lock:
        for conn in _connections.values():
            conn.close()
        _connections.clear()


def execute_query(query: str, params: tuple = (), db_name: str = "agentictrust.db") -> list:
    """Execute a SELECT query and return results.
    
    Args:
        query: SQL query string
        params: Query parameters
        db_name: Database filename
        
    Returns:
        List of row results
    """
    conn = get_connection(db_name)
    cursor = conn.execute(query, params)
    return cursor.fetchall()


def execute_update(query: str, params: tuple = (), db_name: str = "agentictrust.db") -> int:
    """Execute an INSERT/UPDATE/DELETE query.
    
    Args:
        query: SQL query string
        params: Query parameters
        db_name: Database filename
        
    Returns:
        Number of affected rows
    """
    conn = get_connection(db_name)
    cursor = conn.execute(query, params)
    conn.commit()
    return cursor.rowcount


# Context manager for transactions
class transaction:
    """Context manager for database transactions."""
    
    def __init__(self, db_name: str = "agentictrust.db"):
        self.db_name = db_name
        self.conn: Optional[sqlite3.Connection] = None
    
    def __enter__(self) -> sqlite3.Connection:
        self.conn = get_connection(self.db_name)
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback() 