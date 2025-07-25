"""Health check and system information endpoints"""

import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from agentictrust.backend.api.dependencies import DatabaseSession
from agentictrust.backend.config.settings import get_settings
from agentictrust.backend.schemas.responses import HealthResponse, InfoResponse
from agentictrust.backend.core.exceptions import DatabaseError

router = APIRouter()

# Store startup time for uptime calculation
startup_time = time.time()

settings = get_settings()


@router.get("/health", response_model=HealthResponse, summary="Health check endpoint")
async def health_check(db: AsyncSession = DatabaseSession):
    """
    Health check with database connectivity test.
    
    Returns system health status, database connectivity, and schema version.
    """
    try:
        # Test database connectivity
        result = await db.execute(text("SELECT 1"))
        tables_accessible = bool(result.scalar())
        
        # Get schema version (if schema_versions table exists)
        schema_version = None
        try:
            result = await db.execute(text("SELECT MAX(version) FROM schema_versions"))
            schema_version = result.scalar()
        except Exception:
            # Table might not exist yet
            pass
        
        # Calculate uptime
        uptime = time.time() - startup_time
        
        return HealthResponse(
            status="ok",
            database=settings.DATABASE_URL.split("://")[0] + "://***",  # Hide credentials
            schema_version=schema_version,
            tables_accessible=tables_accessible,
            uptime=uptime
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Database error: {str(e)}"
        )


@router.get("/info", response_model=InfoResponse, summary="System information")
async def system_info(db: AsyncSession = DatabaseSession):
    """
    Get comprehensive system information and statistics.
    
    Returns database statistics, configuration, and feature flags.
    """
    try:
        # Get table counts and statistics
        stats: Dict[str, Any] = {}
        tables = ["mcps", "events", "observability", "logs"]
        
        for table in tables:
            try:
                result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[f"{table}_count"] = count if count is not None else 0
            except Exception:
                stats[f"{table}_count"] = "table_not_found"
        
        # Add additional statistics
        stats["uptime"] = time.time() - startup_time
        
        return InfoResponse(
            database_path=settings.DATABASE_URL,
            statistics=stats,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            features={
                "metrics": settings.ENABLE_METRICS,
                "tracing": settings.ENABLE_TRACING,
                "debug": settings.DEBUG,
            }
        )
        
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve system information: {str(e)}")


@router.get("/ready", summary="Readiness probe")
async def readiness_check(db: AsyncSession = DatabaseSession):
    """
    Kubernetes-style readiness probe.
    
    Returns 200 if the service is ready to receive traffic.
    """
    try:
        # Simple database connectivity test
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/live", summary="Liveness probe")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    
    Returns 200 if the service is alive (no database dependency).
    """
    return {"status": "alive", "uptime": time.time() - startup_time} 