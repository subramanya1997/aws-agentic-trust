-- Migration: Add usage tracking tables and update MCP table
-- Date: 2025-05-26

-- Add connection tracking fields to mcps table
ALTER TABLE mcps ADD COLUMN connected_instances INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE mcps ADD COLUMN last_connected_at DATETIME;
ALTER TABLE mcps ADD COLUMN last_disconnected_at DATETIME;
ALTER TABLE mcps ADD COLUMN total_connections INTEGER DEFAULT 0 NOT NULL;

-- Create index for connected_instances
CREATE INDEX idx_mcps_connected_instances ON mcps(connected_instances);

-- Create agent_mcp_usage table
CREATE TABLE agent_mcp_usage (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    mcp_id VARCHAR(36) NOT NULL,
    is_connected VARCHAR(10) DEFAULT 'false' NOT NULL,
    connected_at DATETIME,
    disconnected_at DATETIME,
    total_tool_calls INTEGER DEFAULT 0 NOT NULL,
    total_resource_reads INTEGER DEFAULT 0 NOT NULL,
    total_prompt_gets INTEGER DEFAULT 0 NOT NULL,
    last_activity_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (mcp_id) REFERENCES mcps(id) ON DELETE CASCADE
);

-- Create indexes for agent_mcp_usage
CREATE INDEX idx_agent_mcp_usage_agent ON agent_mcp_usage(agent_id);
CREATE INDEX idx_agent_mcp_usage_mcp ON agent_mcp_usage(mcp_id);
CREATE INDEX idx_agent_mcp_usage_connected ON agent_mcp_usage(is_connected);
CREATE UNIQUE INDEX idx_agent_mcp_usage_unique ON agent_mcp_usage(agent_id, mcp_id);

-- Create agent_tool_usage table
CREATE TABLE agent_tool_usage (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    tool_id VARCHAR(36) NOT NULL,
    total_calls INTEGER DEFAULT 0 NOT NULL,
    last_called_at DATETIME,
    first_called_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES mcp_tools(id) ON DELETE CASCADE
);

-- Create indexes for agent_tool_usage
CREATE INDEX idx_agent_tool_usage_agent ON agent_tool_usage(agent_id);
CREATE INDEX idx_agent_tool_usage_tool ON agent_tool_usage(tool_id);
CREATE UNIQUE INDEX idx_agent_tool_usage_unique ON agent_tool_usage(agent_id, tool_id);

-- Create agent_resource_usage table
CREATE TABLE agent_resource_usage (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    resource_id VARCHAR(36) NOT NULL,
    total_reads INTEGER DEFAULT 0 NOT NULL,
    last_read_at DATETIME,
    first_read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES mcp_resources(id) ON DELETE CASCADE
);

-- Create indexes for agent_resource_usage
CREATE INDEX idx_agent_resource_usage_agent ON agent_resource_usage(agent_id);
CREATE INDEX idx_agent_resource_usage_resource ON agent_resource_usage(resource_id);
CREATE UNIQUE INDEX idx_agent_resource_usage_unique ON agent_resource_usage(agent_id, resource_id);

-- Create agent_prompt_usage table
CREATE TABLE agent_prompt_usage (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    prompt_id VARCHAR(36) NOT NULL,
    total_gets INTEGER DEFAULT 0 NOT NULL,
    last_got_at DATETIME,
    first_got_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (prompt_id) REFERENCES mcp_prompts(id) ON DELETE CASCADE
);

-- Create indexes for agent_prompt_usage
CREATE INDEX idx_agent_prompt_usage_agent ON agent_prompt_usage(agent_id);
CREATE INDEX idx_agent_prompt_usage_prompt ON agent_prompt_usage(prompt_id);
CREATE UNIQUE INDEX idx_agent_prompt_usage_unique ON agent_prompt_usage(agent_id, prompt_id); 