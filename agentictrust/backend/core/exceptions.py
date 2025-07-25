"""Custom exceptions for AgenticTrust backend"""

from typing import Any, Dict, Optional


class AgenticTrustException(Exception):
    """Base exception for AgenticTrust backend"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AgenticTrustException):
    """Resource not found exception"""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status_code=404)


class ValidationError(AgenticTrustException):
    """Data validation error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, status_code=422)


class DatabaseError(AgenticTrustException):
    """Database operation error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, status_code=500)


class ConfigurationError(AgenticTrustException):
    """Configuration error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class ExternalServiceError(AgenticTrustException):
    """External service error"""
    def __init__(self, service: str, message: str):
        full_message = f"External service '{service}' error: {message}"
        super().__init__(full_message, status_code=502) 