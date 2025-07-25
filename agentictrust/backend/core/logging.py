"""Structured logging configuration for AgenticTrust backend"""

import logging
import logging.config
import logging.handlers
import sys
from typing import Dict, Any

from agentictrust.backend.config.settings import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        import json
        
        # Basic log data
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields from record
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        if hasattr(record, "method"):
            log_data["method"] = record.method
        
        if hasattr(record, "url"):
            log_data["url"] = record.url
        
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        
        if hasattr(record, "process_time"):
            log_data["process_time"] = record.process_time
        
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        
        if hasattr(record, "user_agent"):
            log_data["user_agent"] = record.user_agent
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging() -> None:
    """Setup logging configuration"""
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Set formatter based on format preference
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    agentictrust_logger = logging.getLogger("agentictrust")
    agentictrust_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    agentictrust_logger.propagate = False
    agentictrust_logger.addHandler(console_handler)
    
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_logger.propagate = False
    uvicorn_logger.addHandler(console_handler)
    
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.setLevel(logging.WARNING)
    sqlalchemy_logger.propagate = False
    sqlalchemy_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if settings.LOG_FILE:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        file_handler.setFormatter(formatter)
        
        root_logger.addHandler(file_handler)
        agentictrust_logger.addHandler(file_handler)
        uvicorn_logger.addHandler(file_handler)
        sqlalchemy_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name) 