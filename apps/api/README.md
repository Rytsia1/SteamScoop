# SteamScoop API & Worker Service

Backend RESTful API, ingestion pipelines, and asynchronous workers for SteamScoop.

## Tech Stack
- **Framework**: FastAPI (Python 3.11+)
- **ORM & Database**: SQLAlchemy 2.0 with PostgreSQL (psycopg v3)
- **Migrations**: Alembic
- **Task Queue**: Celery with Redis broker
- **Validation**: Pydantic v2
- **Testing & Quality**: pytest, Ruff, mypy

## Local Setup
```bash
# Using uv (recommended)
uv venv --python 3.11
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linter & typechecker
ruff check .
mypy app
```

