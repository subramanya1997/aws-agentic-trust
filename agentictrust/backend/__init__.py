"""AgenticTrust Backend Package

Modern, production-ready FastAPI backend with:
- SQLAlchemy ORM with async support
- Multi-database support (SQLite for dev, PostgreSQL for prod)
- Proper architecture patterns (Repository, Service, etc.)
- Comprehensive logging and error handling
- API versioning
"""

__version__ = "0.4.0"

from .main import app  # re-export for Uvicorn convenience

__all__ = ["app"] 