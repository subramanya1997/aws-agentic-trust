"""Application settings and configuration management"""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings
from agentictrust.backend.data.paths import get_db_path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AgenticTrust Backend"
    VERSION: str = "0.4.0"
    DESCRIPTION: str = "Production-ready backend service for MCP management and monitoring"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    RELOAD: bool = False
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v, values):
        if isinstance(v, str):
            return v
        
        # Auto-generate database URL based on environment
        env = values.get("ENVIRONMENT", "development")
        
        if env == "production":
            # PostgreSQL for production
            db_user = os.getenv("DB_USER", "agentictrust")
            db_password = os.getenv("DB_PASSWORD", "password")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "agentictrust")
            return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            # SQLite for development/testing
            db_path = get_db_path("agentictrust.db")
            return f"sqlite+aiosqlite:///{db_path}"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None
    
    # Feature Flags
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 