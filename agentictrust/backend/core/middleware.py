"""Custom middleware for AgenticTrust backend"""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from agentictrust.backend.core.exceptions import AgenticTrustException
from agentictrust.backend.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with correlation IDs"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                }
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            
            logger.error(
                "Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(exc),
                    "process_time": process_time,
                },
                exc_info=True
            )
            
            # Re-raise to let error handler deal with it
            raise


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except AgenticTrustException as exc:
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            
            logger.error(
                "AgenticTrust exception",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "error_message": exc.message,
                    "error_details": exc.details,
                }
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "type": type(exc).__name__,
                        "message": exc.message,
                        "details": exc.details,
                        "correlation_id": correlation_id,
                    }
                }
            )
        except Exception as exc:
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            
            logger.error(
                "Unhandled exception",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "InternalServerError",
                        "message": "An unexpected error occurred",
                        "correlation_id": correlation_id,
                    }
                }
            )


def add_middleware(app: FastAPI) -> None:
    """Add all middleware to the FastAPI application"""
    
    # Add error handling middleware first (closest to request)
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware) 