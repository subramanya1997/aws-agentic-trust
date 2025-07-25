"""AgenticTrust Backend - FastAPI Application Entry Point

This is the main entry point for the AgenticTrust backend service.
Run with: uvicorn agentictrust.backend.main:app --reload --port 8001
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentictrust.backend.config.settings import get_settings
from agentictrust.backend.config.database import create_tables
from agentictrust.backend.api.v1.router import api_router
from agentictrust.backend.core.middleware import add_middleware
from agentictrust.backend.core.logging import setup_logging

# Initialize settings
settings = get_settings()

# Setup logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="AgenticTrust Backend",
    version="0.4.0",
    description="Production-ready backend service for MCP management and monitoring",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
add_middleware(app)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        await create_tables()
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database tables: {e}")
        # Note: In production, you might want to raise the exception
        # to prevent startup if database is not accessible


@app.get("/")
async def root():
    """Root endpoint with basic service information"""
    return {
        "service": "AgenticTrust Backend",
        "version": "0.4.0",
        "status": "running",
        "docs": "/docs",
        "api": settings.API_V1_STR
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agentictrust.backend.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 