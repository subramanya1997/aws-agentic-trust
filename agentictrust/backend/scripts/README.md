# AgenticTrust Backend Scripts

This directory contains utility scripts for managing the AgenticTrust backend.

## cleanup_database.py

A comprehensive database cleanup script that helps maintain database integrity by:

### Features

1. **Removes orphaned capabilities**
   - Tools, resources, and prompts from deleted MCPs
   - Shows which items will be removed

2. **Cleans usage tracking records**
   - Removes tracking records for deleted agents or capabilities
   - Cleans up MCP, tool, resource, and prompt usage records

3. **Updates agent permissions**
   - Removes references to deleted capabilities from agent permissions
   - Ensures agents only reference existing tools, resources, and prompts

4. **Optionally removes old logs**
   - Can clean up log entries older than a specified number of days
   - Helps manage database size

### Usage

The script can be run in two ways:

**From the project root directory:**
```bash
# Always start with a dry run to see what will be cleaned
python -m agentictrust.backend.scripts.cleanup_database --dry-run

# Actually perform the cleanup
python -m agentictrust.backend.scripts.cleanup_database --execute

# Clean up including logs older than 7 days
python -m agentictrust.backend.scripts.cleanup_database --execute --clean-logs --log-days 7
```

**From the backend directory:**
```bash
cd agentictrust/backend

# Always start with a dry run to see what will be cleaned
python scripts/cleanup_database.py --dry-run

# Actually perform the cleanup
python scripts/cleanup_database.py --execute

# Get help
python scripts/cleanup_database.py --help
```

### Command-line Options

- `--dry-run` (default): Preview changes without modifying the database
- `--execute`: Actually perform the cleanup (disables dry-run)
- `--clean-logs`: Also clean up old log entries
- `--log-days N`: Number of days to keep logs (default: 30)

### Safety Features

- **Dry-run by default**: The script runs in dry-run mode by default to prevent accidental data loss
- **Transaction support**: All changes are wrapped in a database transaction
- **Detailed reporting**: Shows exactly what will be or was cleaned
- **Summary statistics**: Provides a clear summary of all cleanup operations

### Example Output

```
DRY RUN MODE - Database Cleanup Starting...

1. Checking for orphaned capabilities...
Would remove 16 orphaned tools
  - contacts (MCP: a9b22f55-a834-430a-87ef-947585cd067f)
  - notes (MCP: a9b22f55-a834-430a-87ef-947585cd067f)
  ... and 14 more

2. Checking for orphaned usage tracking records...
Would remove 5 orphaned MCP usage records
Would remove 12 orphaned tool usage records

3. Checking agent permissions...
  Agent 'Workspan agent': Removing 2 invalid tool IDs
Would update 1 agents with invalid capability references

🔍 Dry run complete. No changes were made.

==================================================
CLEANUP SUMMARY
==================================================
📊 Total items to be cleaned: 34

Details:
  - Orphaned tools: 16
  - Orphaned MCP usage records: 5
  - Orphaned tool usage records: 12
  - Agents with updated permissions: 1
==================================================
```

### When to Run

Consider running this cleanup script:
- After deleting MCP servers
- After major configuration changes
- As part of regular maintenance (e.g., monthly)
- When the database size grows too large due to logs

### Database Location

The script uses the AgenticTrust database location configured in your environment:
- Default: `~/.agentictrust/db/agentictrust.db`
- Can be overridden with `AGENTICTRUST_DB_PATH` environment variable 