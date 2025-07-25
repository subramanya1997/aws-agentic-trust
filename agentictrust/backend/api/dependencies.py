"""Dependency injection for AgenticTrust backend API"""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agentictrust.backend.config.database import get_db


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency"""
    async for session in get_db():
        yield session


# Commonly used dependencies
DatabaseSession = Depends(get_database_session) 