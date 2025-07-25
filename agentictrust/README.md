# AgenticTrust Backend

Production-ready backend service for MCP (Model Context Protocol) management and monitoring.

## Features

- FastAPI-based REST API
- SQLAlchemy ORM with SQLite/PostgreSQL support
- Pydantic data validation and settings management
- Async/await support throughout
- Comprehensive test suite
- Code formatting and linting

## Installation

Using UV (recommended):

```bash
uv sync --all-extras
```

Using pip:

```bash
pip install -e .
```

## Development

1. Install dependencies:
   ```bash
   uv sync --all-extras
   ```

2. Run the development server:
   ```bash
   uv run uvicorn agentictrust.backend.main:app --reload --port 8000
   ```

3. Run tests:
   ```bash
   uv run pytest
   ```

4. Format code:
   ```bash
   uv run black .
   uv run isort .
   ```

5. Lint code:
   ```bash
   uv run flake8 .
   ```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License 