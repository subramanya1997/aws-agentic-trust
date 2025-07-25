"""Log entry management endpoints"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from agentictrust.backend.api.dependencies import DatabaseSession
from agentictrust.backend.schemas.logs import (
    LogEntryCreate,
    LogEntryResponse,
    LogEntryListResponse,
    LogBatchRequest
)
from agentictrust.backend.schemas.responses import SuccessResponse
from agentictrust.backend.data.models.logs import LogEntry
from agentictrust.backend.core.exceptions import DatabaseError

router = APIRouter()


@router.get("/", response_model=LogEntryListResponse, summary="Retrieve logs")
async def list_logs(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: AsyncSession = DatabaseSession
):
    """Retrieve logs with optional filtering and pagination."""
    try:
        # Build query
        query = select(LogEntry)
        
        # Apply filters
        if event_type:
            query = query.where(LogEntry.event_type == event_type)
        if severity:
            query = query.where(LogEntry.severity == severity)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering (newest first)
        query = query.order_by(LogEntry.created_at.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Convert to response models
        items = [LogEntryResponse.from_orm(log) for log in logs]
        
        return LogEntryListResponse(
            items=items,
            total=total,
            page=(skip // limit) + 1,
            size=limit
        )
        
    except Exception as e:
        raise DatabaseError(f"Failed to list logs: {str(e)}")


@router.post("/batch", response_model=SuccessResponse, summary="Ingest batch of logs")
async def ingest_logs_batch(
    batch_request: LogBatchRequest,
    db: AsyncSession = DatabaseSession
):
    """Ingest a batch of log entries."""
    try:
        # Create log entries
        log_entries = []
        for log_data in batch_request.logs:
            log_entry = LogEntry(
                timestamp=log_data.timestamp,
                event_type=log_data.event_type,
                data=log_data.data,
                correlation_id=log_data.correlation_id,
                session_id=log_data.session_id,
                source=log_data.source,
                severity=log_data.severity
            )
            log_entries.append(log_entry)
        
        # Add all entries to database
        db.add_all(log_entries)
        await db.commit()
        
        return SuccessResponse(
            message=f"Successfully ingested {len(log_entries)} log entries"
        )
        
    except Exception as e:
        await db.rollback()
        raise DatabaseError(f"Failed to ingest logs: {str(e)}")


@router.get("/stats", summary="Get log statistics")
async def get_log_stats(db: AsyncSession = DatabaseSession):
    """Get statistics about log entries."""
    try:
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import and_
        
        # Get total count
        total_query = select(func.count(LogEntry.id))
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # Get counts by event type
        event_type_query = select(
            LogEntry.event_type,
            func.count(LogEntry.id).label('count')
        ).group_by(LogEntry.event_type)
        
        event_type_result = await db.execute(event_type_query)
        event_type_counts = {row.event_type: row.count for row in event_type_result}
        
        # Get counts by severity
        severity_query = select(
            LogEntry.severity,
            func.count(LogEntry.id).label('count')
        ).group_by(LogEntry.severity)
        
        severity_result = await db.execute(severity_query)
        severity_counts = {row.severity: row.count for row in severity_result}
        
        error_count = severity_counts.get("error", 0) + severity_counts.get("critical", 0)
        
        # Trend calculations (last 7 days vs previous 7 days)
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # Recent logs (last 7 days)
        recent_count = (
            await db.execute(
                select(func.count(LogEntry.id))
                .where(LogEntry.created_at >= week_ago.isoformat())
            )
        ).scalar()
        
        # Previous week logs (8-14 days ago)
        previous_week_count = (
            await db.execute(
                select(func.count(LogEntry.id))
                .where(and_(
                    LogEntry.created_at >= two_weeks_ago.isoformat(),
                    LogEntry.created_at < week_ago.isoformat()
                ))
            )
        ).scalar()
        
        # Recent errors (last 7 days)
        recent_errors = (
            await db.execute(
                select(func.count(LogEntry.id))
                .where(and_(
                    LogEntry.created_at >= week_ago.isoformat(),
                    LogEntry.severity.in_(["error", "critical"])
                ))
            )
        ).scalar()
        
        # Previous week errors (8-14 days ago)
        previous_week_errors = (
            await db.execute(
                select(func.count(LogEntry.id))
                .where(and_(
                    LogEntry.created_at >= two_weeks_ago.isoformat(),
                    LogEntry.created_at < week_ago.isoformat(),
                    LogEntry.severity.in_(["error", "critical"])
                ))
            )
        ).scalar()
        
        # Calculate success rate trends
        recent_success_rate = ((recent_count - recent_errors) / recent_count * 100) if recent_count > 0 else 100
        previous_success_rate = ((previous_week_count - previous_week_errors) / previous_week_count * 100) if previous_week_count > 0 else 100
        success_rate_trend = recent_success_rate - previous_success_rate
        
        return {
            "total": total,
            "by_event_type": event_type_counts,
            "by_severity": severity_counts,
            "error_count": error_count,
            "trends": {
                "recent_logs": recent_count,
                "previous_week_logs": previous_week_count,
                "recent_errors": recent_errors,
                "previous_week_errors": previous_week_errors,
                "success_rate_trend": round(success_rate_trend, 1),
                "is_improving": success_rate_trend >= 0,
            },
        }
        
    except Exception as e:
        raise DatabaseError(f"Failed to get log statistics: {str(e)}") 