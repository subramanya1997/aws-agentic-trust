#!/usr/bin/env python3
"""
Database Cleanup Script for AgenticTrust

This script performs various cleanup operations on the AgenticTrust database:
1. Removes orphaned tools, resources, and prompts from deleted MCPs
2. Cleans up usage tracking records for deleted entities
3. Updates agent permissions to remove references to deleted capabilities
4. Optionally removes old log entries
5. Provides a dry-run mode to preview changes

Usage:
    # From project root:
    python -m agentictrust.backend.scripts.cleanup_database [--dry-run] [--clean-logs] [--log-days 30]
    
    # Or from backend directory:
    python scripts/cleanup_database.py [--dry-run] [--clean-logs] [--log-days 30]
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Set, Dict, Any

# Determine how to import based on execution context
if __name__ == "__main__" and not __package__:
    # Running as a script, add paths appropriately
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent
    
    # Try to import as if running from project root first
    sys.path.insert(0, str(project_root))
    try:
        from agentictrust.backend.config.database import AsyncSessionLocal
        from agentictrust.backend.data.models.mcp import MCP
        from agentictrust.backend.data.models.tool import Tool
        from agentictrust.backend.data.models.resource import Resource
        from agentictrust.backend.data.models.prompt import Prompt
        from agentictrust.backend.data.models.agent import Agent
        from agentictrust.backend.data.models.logs import LogEntry
        from agentictrust.backend.data.models.usage_tracking import (
            AgentMCPUsage,
            AgentToolUsage,
            AgentResourceUsage,
            AgentPromptUsage,
        )
    except ImportError:
        # Fallback to backend directory imports
        sys.path.insert(0, str(backend_dir))
        from config.database import AsyncSessionLocal
        from data.models.mcp import MCP
        from data.models.tool import Tool
        from data.models.resource import Resource
        from data.models.prompt import Prompt
        from data.models.agent import Agent
        from data.models.logs import LogEntry
        from data.models.usage_tracking import (
            AgentMCPUsage,
            AgentToolUsage,
            AgentResourceUsage,
            AgentPromptUsage,
        )
else:
    # Running as a module
    from agentictrust.backend.config.database import AsyncSessionLocal
    from agentictrust.backend.data.models.mcp import MCP
    from agentictrust.backend.data.models.tool import Tool
    from agentictrust.backend.data.models.resource import Resource
    from agentictrust.backend.data.models.prompt import Prompt
    from agentictrust.backend.data.models.agent import Agent
    from agentictrust.backend.data.models.logs import LogEntry
    from agentictrust.backend.data.models.usage_tracking import (
        AgentMCPUsage,
        AgentToolUsage,
        AgentResourceUsage,
        AgentPromptUsage,
    )

from sqlalchemy import select, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseCleaner:
    """Handles database cleanup operations"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.stats = {
            "orphaned_tools": 0,
            "orphaned_resources": 0,
            "orphaned_prompts": 0,
            "orphaned_mcp_usage": 0,
            "orphaned_tool_usage": 0,
            "orphaned_resource_usage": 0,
            "orphaned_prompt_usage": 0,
            "updated_agents": 0,
            "cleaned_logs": 0,
        }
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        async with AsyncSessionLocal() as session:
            return session
    
    async def find_orphaned_capabilities(self, session: AsyncSession) -> Dict[str, List[str]]:
        """Find tools, resources, and prompts that belong to non-existent MCPs"""
        
        # Get all MCP IDs
        mcp_ids = set((await session.execute(select(MCP.id))).scalars().all())
        
        # Find orphaned tools
        orphaned_tools = (await session.execute(
            select(Tool.id, Tool.name, Tool.mcp_id)
            .where(~Tool.mcp_id.in_(mcp_ids))
        )).all()
        
        # Find orphaned resources
        orphaned_resources = (await session.execute(
            select(Resource.id, Resource.name, Resource.mcp_id)
            .where(~Resource.mcp_id.in_(mcp_ids))
        )).all()
        
        # Find orphaned prompts
        orphaned_prompts = (await session.execute(
            select(Prompt.id, Prompt.name, Prompt.mcp_id)
            .where(~Prompt.mcp_id.in_(mcp_ids))
        )).all()
        
        return {
            "tools": [(t.id, t.name, t.mcp_id) for t in orphaned_tools],
            "resources": [(r.id, r.name, r.mcp_id) for r in orphaned_resources],
            "prompts": [(p.id, p.name, p.mcp_id) for p in orphaned_prompts],
        }
    
    async def clean_orphaned_capabilities(self, session: AsyncSession, orphaned: Dict[str, List]) -> None:
        """Remove orphaned capabilities"""
        
        # Clean tools
        if orphaned["tools"]:
            tool_ids = [t[0] for t in orphaned["tools"]]
            if not self.dry_run:
                await session.execute(delete(Tool).where(Tool.id.in_(tool_ids)))
            self.stats["orphaned_tools"] = len(tool_ids)
            print(f"{'Would remove' if self.dry_run else 'Removed'} {len(tool_ids)} orphaned tools")
            for tool_id, name, mcp_id in orphaned["tools"][:5]:  # Show first 5
                print(f"  - {name} (MCP: {mcp_id})")
            if len(orphaned["tools"]) > 5:
                print(f"  ... and {len(orphaned['tools']) - 5} more")
        
        # Clean resources
        if orphaned["resources"]:
            resource_ids = [r[0] for r in orphaned["resources"]]
            if not self.dry_run:
                await session.execute(delete(Resource).where(Resource.id.in_(resource_ids)))
            self.stats["orphaned_resources"] = len(resource_ids)
            print(f"{'Would remove' if self.dry_run else 'Removed'} {len(resource_ids)} orphaned resources")
        
        # Clean prompts
        if orphaned["prompts"]:
            prompt_ids = [p[0] for p in orphaned["prompts"]]
            if not self.dry_run:
                await session.execute(delete(Prompt).where(Prompt.id.in_(prompt_ids)))
            self.stats["orphaned_prompts"] = len(prompt_ids)
            print(f"{'Would remove' if self.dry_run else 'Removed'} {len(prompt_ids)} orphaned prompts")
    
    async def clean_orphaned_usage_tracking(self, session: AsyncSession) -> None:
        """Clean up usage tracking records for deleted entities"""
        
        # Clean MCP usage for non-existent MCPs or agents
        mcp_ids = set((await session.execute(select(MCP.id))).scalars().all())
        agent_ids = set((await session.execute(select(Agent.id))).scalars().all())
        
        orphaned_mcp_usage = await session.execute(
            select(func.count()).select_from(AgentMCPUsage)
            .where(or_(
                ~AgentMCPUsage.mcp_id.in_(mcp_ids),
                ~AgentMCPUsage.agent_id.in_(agent_ids)
            ))
        )
        count = orphaned_mcp_usage.scalar() or 0
        if count > 0:
            if not self.dry_run:
                await session.execute(
                    delete(AgentMCPUsage).where(or_(
                        ~AgentMCPUsage.mcp_id.in_(mcp_ids),
                        ~AgentMCPUsage.agent_id.in_(agent_ids)
                    ))
                )
            self.stats["orphaned_mcp_usage"] = count
            print(f"{'Would remove' if self.dry_run else 'Removed'} {count} orphaned MCP usage records")
        
        # Clean tool usage for non-existent tools or agents
        tool_ids = set((await session.execute(select(Tool.id))).scalars().all())
        
        orphaned_tool_usage = await session.execute(
            select(func.count()).select_from(AgentToolUsage)
            .where(or_(
                ~AgentToolUsage.tool_id.in_(tool_ids),
                ~AgentToolUsage.agent_id.in_(agent_ids)
            ))
        )
        count = orphaned_tool_usage.scalar() or 0
        if count > 0:
            if not self.dry_run:
                await session.execute(
                    delete(AgentToolUsage).where(or_(
                        ~AgentToolUsage.tool_id.in_(tool_ids),
                        ~AgentToolUsage.agent_id.in_(agent_ids)
                    ))
                )
            self.stats["orphaned_tool_usage"] = count
            print(f"{'Would remove' if self.dry_run else 'Removed'} {count} orphaned tool usage records")
        
        # Similar for resources and prompts
        resource_ids = set((await session.execute(select(Resource.id))).scalars().all())
        prompt_ids = set((await session.execute(select(Prompt.id))).scalars().all())
        
        # Clean resource usage
        orphaned_resource_usage = await session.execute(
            select(func.count()).select_from(AgentResourceUsage)
            .where(or_(
                ~AgentResourceUsage.resource_id.in_(resource_ids),
                ~AgentResourceUsage.agent_id.in_(agent_ids)
            ))
        )
        count = orphaned_resource_usage.scalar() or 0
        if count > 0:
            if not self.dry_run:
                await session.execute(
                    delete(AgentResourceUsage).where(or_(
                        ~AgentResourceUsage.resource_id.in_(resource_ids),
                        ~AgentResourceUsage.agent_id.in_(agent_ids)
                    ))
                )
            self.stats["orphaned_resource_usage"] = count
            print(f"{'Would remove' if self.dry_run else 'Removed'} {count} orphaned resource usage records")
        
        # Clean prompt usage
        orphaned_prompt_usage = await session.execute(
            select(func.count()).select_from(AgentPromptUsage)
            .where(or_(
                ~AgentPromptUsage.prompt_id.in_(prompt_ids),
                ~AgentPromptUsage.agent_id.in_(agent_ids)
            ))
        )
        count = orphaned_prompt_usage.scalar() or 0
        if count > 0:
            if not self.dry_run:
                await session.execute(
                    delete(AgentPromptUsage).where(or_(
                        ~AgentPromptUsage.prompt_id.in_(prompt_ids),
                        ~AgentPromptUsage.agent_id.in_(agent_ids)
                    ))
                )
            self.stats["orphaned_prompt_usage"] = count
            print(f"{'Would remove' if self.dry_run else 'Removed'} {count} orphaned prompt usage records")
    
    async def update_agent_permissions(self, session: AsyncSession) -> None:
        """Update agents to remove references to deleted capabilities"""
        
        # Get valid IDs
        valid_tool_ids = set((await session.execute(select(Tool.id))).scalars().all())
        valid_resource_ids = set((await session.execute(select(Resource.id))).scalars().all())
        valid_prompt_ids = set((await session.execute(select(Prompt.id))).scalars().all())
        
        # Get all agents
        agents = (await session.execute(select(Agent))).scalars().all()
        
        updated_count = 0
        for agent in agents:
            updated = False
            
            # Clean tool permissions
            if agent.allowed_tool_ids:
                valid_tools = [tid for tid in agent.allowed_tool_ids if tid in valid_tool_ids]
                if len(valid_tools) != len(agent.allowed_tool_ids):
                    print(f"  Agent '{agent.name}': Removing {len(agent.allowed_tool_ids) - len(valid_tools)} invalid tool IDs")
                    if not self.dry_run:
                        agent.allowed_tool_ids = valid_tools
                    updated = True
            
            # Clean resource permissions
            if agent.allowed_resource_ids:
                valid_resources = [rid for rid in agent.allowed_resource_ids if rid in valid_resource_ids]
                if len(valid_resources) != len(agent.allowed_resource_ids):
                    print(f"  Agent '{agent.name}': Removing {len(agent.allowed_resource_ids) - len(valid_resources)} invalid resource IDs")
                    if not self.dry_run:
                        agent.allowed_resource_ids = valid_resources
                    updated = True
            
            # Clean prompt permissions
            if agent.allowed_prompt_ids:
                valid_prompts = [pid for pid in agent.allowed_prompt_ids if pid in valid_prompt_ids]
                if len(valid_prompts) != len(agent.allowed_prompt_ids):
                    print(f"  Agent '{agent.name}': Removing {len(agent.allowed_prompt_ids) - len(valid_prompts)} invalid prompt IDs")
                    if not self.dry_run:
                        agent.allowed_prompt_ids = valid_prompts
                    updated = True
            
            if updated:
                updated_count += 1
        
        if updated_count > 0:
            self.stats["updated_agents"] = updated_count
            print(f"{'Would update' if self.dry_run else 'Updated'} {updated_count} agents with invalid capability references")
    
    async def clean_old_logs(self, session: AsyncSession, days: int) -> None:
        """Remove log entries older than specified days"""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Count logs to be deleted
        old_logs_count = await session.execute(
            select(func.count()).select_from(LogEntry)
            .where(LogEntry.created_at < cutoff_date)
        )
        count = old_logs_count.scalar() or 0
        
        if count > 0:
            if not self.dry_run:
                await session.execute(
                    delete(LogEntry).where(LogEntry.created_at < cutoff_date)
                )
            self.stats["cleaned_logs"] = count
            print(f"{'Would remove' if self.dry_run else 'Removed'} {count} log entries older than {days} days")
    
    async def run_cleanup(self, clean_logs: bool = False, log_days: int = 30) -> None:
        """Run all cleanup operations"""
        
        print(f"\n{'DRY RUN MODE' if self.dry_run else 'CLEANUP MODE'} - Database Cleanup Starting...\n")
        
        async with AsyncSessionLocal() as session:
            try:
                # Find and clean orphaned capabilities
                print("1. Checking for orphaned capabilities...")
                orphaned = await self.find_orphaned_capabilities(session)
                await self.clean_orphaned_capabilities(session, orphaned)
                
                # Clean orphaned usage tracking
                print("\n2. Checking for orphaned usage tracking records...")
                await self.clean_orphaned_usage_tracking(session)
                
                # Update agent permissions
                print("\n3. Checking agent permissions...")
                await self.update_agent_permissions(session)
                
                # Clean old logs if requested
                if clean_logs:
                    print(f"\n4. Checking for logs older than {log_days} days...")
                    await self.clean_old_logs(session, log_days)
                
                # Commit changes if not dry run
                if not self.dry_run:
                    await session.commit()
                    print("\n✅ All changes committed successfully!")
                else:
                    print("\n🔍 Dry run complete. No changes were made.")
                
                # Print summary
                self.print_summary()
                
            except Exception as e:
                if not self.dry_run:
                    await session.rollback()
                print(f"\n❌ Error during cleanup: {e}")
                raise
    
    def print_summary(self) -> None:
        """Print cleanup summary"""
        
        print("\n" + "="*50)
        print("CLEANUP SUMMARY")
        print("="*50)
        
        total_changes = sum(self.stats.values())
        
        if total_changes == 0:
            print("✨ Database is clean! No cleanup needed.")
        else:
            print(f"📊 Total items {'to be cleaned' if self.dry_run else 'cleaned'}: {total_changes}")
            print("\nDetails:")
            
            if self.stats["orphaned_tools"]:
                print(f"  - Orphaned tools: {self.stats['orphaned_tools']}")
            if self.stats["orphaned_resources"]:
                print(f"  - Orphaned resources: {self.stats['orphaned_resources']}")
            if self.stats["orphaned_prompts"]:
                print(f"  - Orphaned prompts: {self.stats['orphaned_prompts']}")
            if self.stats["orphaned_mcp_usage"]:
                print(f"  - Orphaned MCP usage records: {self.stats['orphaned_mcp_usage']}")
            if self.stats["orphaned_tool_usage"]:
                print(f"  - Orphaned tool usage records: {self.stats['orphaned_tool_usage']}")
            if self.stats["orphaned_resource_usage"]:
                print(f"  - Orphaned resource usage records: {self.stats['orphaned_resource_usage']}")
            if self.stats["orphaned_prompt_usage"]:
                print(f"  - Orphaned prompt usage records: {self.stats['orphaned_prompt_usage']}")
            if self.stats["updated_agents"]:
                print(f"  - Agents with updated permissions: {self.stats['updated_agents']}")
            if self.stats["cleaned_logs"]:
                print(f"  - Old log entries removed: {self.stats['cleaned_logs']}")
        
        print("="*50)


async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Clean up the AgenticTrust database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be cleaned
  python cleanup_database.py --dry-run
  
  # Actually perform cleanup
  python cleanup_database.py
  
  # Clean up including logs older than 7 days
  python cleanup_database.py --clean-logs --log-days 7
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without modifying the database (default: True)",
    )
    
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the cleanup (disables dry-run)",
    )
    
    parser.add_argument(
        "--clean-logs",
        action="store_true",
        help="Also clean up old log entries",
    )
    
    parser.add_argument(
        "--log-days",
        type=int,
        default=30,
        help="Number of days to keep logs (default: 30)",
    )
    
    args = parser.parse_args()
    
    # If --execute is specified, disable dry run
    dry_run = not args.execute
    
    cleaner = DatabaseCleaner(dry_run=dry_run)
    await cleaner.run_cleanup(clean_logs=args.clean_logs, log_days=args.log_days)


if __name__ == "__main__":
    asyncio.run(main()) 