-- AgenticTrust Canonical Database Schema
-- This file defines the complete database schema used by all components.
-- Changes here affect both proxy and backend services.

-- =====================================================================
-- UPSTREAM SERVERS REGISTRY
-- =====================================================================

-- Registered upstream MCP servers
CREATE TABLE IF NOT EXISTS upstreams (
    id TEXT PRIMARY KEY,
    command TEXT NOT NULL,
    args TEXT NOT NULL,  -- JSON array of command args
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_upstreams_created ON upstreams(created_at);

-- =====================================================================
-- MCP EVENT STORE (for resumability)
-- =====================================================================

-- Raw JSON-RPC messages for HTTP/SSE resumability
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    stream_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    message_type TEXT NOT NULL,
    method TEXT,
    message_data TEXT NOT NULL,  -- Complete JSON-RPC message
    synced INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_events_stream_timestamp ON events(stream_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_synced ON events(synced);
CREATE INDEX IF NOT EXISTS idx_events_method ON events(method);

-- =====================================================================
-- OBSERVABILITY & ANALYTICS
-- =====================================================================

-- Processed observability insights extracted from events
CREATE TABLE IF NOT EXISTS observability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT,  -- Optional reference to events table
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON data specific to event_type
    synced INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_observability_synced ON observability(synced);
CREATE INDEX IF NOT EXISTS idx_observability_type ON observability(event_type);
CREATE INDEX IF NOT EXISTS idx_observability_timestamp ON observability(timestamp);
CREATE INDEX IF NOT EXISTS idx_observability_event_id ON observability(event_id);

-- =====================================================================
-- BACKEND LOGS (legacy, will be merged with observability)
-- =====================================================================

-- Backend service logs (keeping for backward compatibility)
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON payload
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_type ON logs(event_type);

-- =====================================================================
-- METADATA & HOUSEKEEPING  
-- =====================================================================

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
);

-- Insert initial schema version if not exists
INSERT OR IGNORE INTO schema_versions (version, description) 
VALUES (1, 'Initial schema with upstreams, events, observability, logs');

-- =====================================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================================

-- Combined view of all telemetry data
CREATE VIEW IF NOT EXISTS telemetry_unified AS
SELECT 
    'observability' as source,
    id as source_id,
    timestamp,
    event_type,
    data,
    synced,
    created_at
FROM observability
UNION ALL
SELECT 
    'logs' as source,
    id as source_id,
    timestamp,
    event_type, 
    data,
    0 as synced,  -- logs don't have sync status
    created_at
FROM logs
ORDER BY timestamp DESC;

-- Event statistics view
CREATE VIEW IF NOT EXISTS event_stats AS
SELECT 
    event_type,
    COUNT(*) as count,
    MIN(timestamp) as first_seen,
    MAX(timestamp) as last_seen,
    SUM(CASE WHEN synced = 0 THEN 1 ELSE 0 END) as unsynced_count
FROM observability 
GROUP BY event_type
ORDER BY count DESC; 