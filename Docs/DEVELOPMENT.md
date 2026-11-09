# SteamScoop — Development Environment Guide

**Document:** `Docs/DEVELOPMENT.md`  
**Audience:** Full-Stack Engineers, DevOps Engineers, and Contributors  
**Scope:** Local development, container orchestration, environment configuration, dependency management, and verification.

---

## 1. Prerequisites & Tooling Baseline

To develop on SteamScoop, ensure your workstation meets the following minimum toolchain:

| Tool | Minimum Version | Purpose | Installation / Check |
| :--- | :--- | :--- | :--- |
| **Docker & Compose** | Docker 24+, Compose v2.20+ | Multi-container ecosystem | `docker compose version` |
| **Python** | 3.11+ (CPython) | Backend API, workers, and ML tooling | `python --version` |
| **uv** *(Recommended)* | 0.4+ | Fast Python dependency & venv management | `uv --version` |
| **Node.js & npm** | Node 20 LTS, npm 10+ | React Web Frontend SPA | `node -v && npm -v` |
| **Git** | 2.40+ | Version control | `git --version` |

---

## 2. Quick Start (Containerized Ecosystem)

The primary and recommended workflow for local development uses Docker Compose:

### Step 1: Initialize Configuration
Copy the configuration template to `.env`:
```bash
# On Linux / macOS / Git Bash:
cp .env.example .env

# On Windows PowerShell:
Copy-Item .env.example .env
```

### Step 2: Start All Services
```bash
# Using Make:
make up

# Using PowerShell:
.\scripts\dev.ps1 up

# Direct Docker Compose:
docker compose up -d --build
```

### Step 3: Verify Status & Health
```bash
# Check container status
docker compose ps
```
All containers should display `(healthy)` or `Up`:
- `steamscoop-db`: PostgreSQL 15 (accepting connections on host port 5433)
- `steamscoop-redis`: Redis 7 (broker & cache on host port 6379)
- `steamscoop-api`: FastAPI backend with automatic Alembic migrations (port 8000)
- `steamscoop-worker`: Celery worker connected to Redis broker (health-checked)
- `steamscoop-beat`: Celery beat periodic scheduler
- `steamscoop-web`: React SPA served through Nginx reverse proxy (port 3000)

### Step 4: Access Application Interfaces
- **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health & Subsystems**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Web Frontend Application**: [http://localhost:3000](http://localhost:3000)

---

## 3. Service Startup Dependencies & Lifecycle

Container startup dependencies are orchestrated explicitly to prevent race conditions:

```mermaid
flowchart TD
    db["steamscoop-db\n(PostgreSQL 15)"] -- condition: service_healthy --> api["steamscoop-api\n(Alembic Migration & FastAPI)"]
    redis["steamscoop-redis\n(Redis 7)"] -- condition: service_healthy --> api
    db -- condition: service_healthy --> worker["steamscoop-worker\n(Celery Worker)"]
    redis -- condition: service_healthy --> worker
    redis -- condition: service_healthy --> beat["steamscoop-beat\n(Celery Beat)"]
    api -- condition: service_healthy --> web["steamscoop-web\n(React + Nginx SPA)"]
```

1. **Database & Cache First**: `db` and `redis` boot and must pass their internal healthchecks (`pg_isready` and `redis-cli ping`).
2. **Schema Migration & API**: `api` waits until `db` and `redis` are healthy. It executes `alembic upgrade head` before binding `uvicorn` on port 8000.
3. **Workers & Frontend**: `worker` boots with Celery inspection ping healthchecks; `web` starts only once `api` passes its healthcheck.

---

## 4. Environment Variables Dictionary

The application uses typed **Pydantic Settings** (`apps/api/app/core/config.py`). All variables are documented in `.env.example`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `development` | Environment tier: `development`, `testing`, `staging`, `production`. |
| `DEBUG` | `true` | Enables FastAPI auto-reload and verbose error messages (must be `false` in production). |
| `LOG_LEVEL` | `INFO` | Console logging threshold (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `API_PORT` | `8000` | Host port exposed for FastAPI REST API. |
| `WEB_PORT` | `3000` | Host port exposed for the React Nginx container. |
| `DB_PORT` | `5433` | Host port for PostgreSQL (set to 5433 to avoid collision with native PostgreSQL on 5432). |
| `REDIS_PORT` | `6379` | Host port for Redis broker & cache. |
| `POSTGRES_USER` | `user` | PostgreSQL database user. |
| `POSTGRES_PASSWORD` | `password` | PostgreSQL database password. |
| `POSTGRES_DB` | `steamscoop` | Primary database name. |
| `DATABASE_URL` | `postgresql+psycopg://...` | Connection URI for host tools (e.g. host Alembic, tests). Injected automatically in Docker. |
| `REDIS_URL` | `redis://localhost:6379/0` | Connection URI for Redis host access. Injected automatically in Docker. |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated list or JSON array of allowed frontend origins. |
| `SECRET_KEY` | *(dummy secret)* | HMAC session signing key. Must be a secure random secret in production. |
| `STEAM_API_KEY` | *(placeholder)* | Steam Web API Key from https://steamcommunity.com/dev/apikey. |

---

## 5. Diagnostic Environment Validation

To automatically diagnose configuration syntax, database reachability, and Redis broker connectivity, run the built-in diagnostic tool:

```bash
# Using Make:
make validate-env

# Using PowerShell:
.\scripts\dev.ps1 validate-env

# Direct Python:
python scripts/validate_env.py
```

### Diagnostic Output Example:
```text
======================================================================
 SteamScoop Environment & Dependency Diagnostic Validation
======================================================================
[+] .env file: FOUND (/path/to/steamscoop/.env)
[+] Settings Model: Successfully parsed via Pydantic Settings
    - APP_NAME: SteamScoop API
    - APP_VERSION: 0.1.0
    - APP_ENV: development
    - DEBUG: True
    - CORS_ORIGINS: ['http://localhost:5173', 'http://localhost:3000', 'http://localhost']

--- Subsystem Connectivity Probes ---
[+] PostgreSQL Database: CONNECTED (localhost:5433/steamscoop)
[+] Redis Broker & Cache: CONNECTED (redis://localhost:6379/0)
[+] Frontend Environment: Template present (.env.example)

======================================================================
Result: ALL CHECKS PASSED - Development environment is healthy.
======================================================================
```

---

## 6. Health Checks & Observability

SteamScoop implements a multi-tier health and readiness strategy:

| Endpoint | Target Consumer | Purpose & Behavior |
| :--- | :--- | :--- |
| `GET /health` | Docker / K8s Liveness Probe | Extremely lightweight root check; returns `{"status": "ok"}`. |
| `GET /api/v1/health` | Dashboards & Developers | Comprehensive response envelope reporting status, version, server time, and dependency probes (`database: "connected"`, `redis: "connected"`). Returns `status: "healthy"` or `"degraded"`. |
| `GET /api/v1/health/liveness` | Service Orchestration | Liveness probe returning HTTP 200 `{"status": "ok"}`. |
| `GET /api/v1/health/readiness` | Load Balancers / Traffic Routers | Readiness probe verifying DB & Redis connectivity. Returns HTTP 200 when operational; returns HTTP 503 `SERVICE_UNAVAILABLE` if a critical dependency is down. |

---

## 7. Unified Developer Command Reference

A standardized set of developer commands is provided across platforms:

| Command Purpose | Linux / macOS / Git Bash (`make`) | Windows PowerShell (`.\scripts\dev.ps1`) |
| :--- | :--- | :--- |
| **Bootstrap environment** | `make dev-setup` | `.\scripts\dev.ps1 setup` |
| **Validate configuration** | `make validate-env` | `.\scripts\dev.ps1 validate-env` |
| **Start Docker services** | `make up` | `.\scripts\dev.ps1 up` |
| **Stop Docker services** | `make down` | `.\scripts\dev.ps1 down` |
| **Wipe volumes & restart** | `make down-v` | `.\scripts\dev.ps1 down-v` |
| **Check service health** | `make ps` | `.\scripts\dev.ps1 ps` |
| **Stream container logs** | `make logs` | `.\scripts\dev.ps1 logs` |
| **Run linters** | `make lint` | `.\scripts\dev.ps1 lint` |
| **Format code** | `make format` | `.\scripts\dev.ps1 format` |
| **Static typecheck** | `make typecheck` | `.\scripts\dev.ps1 typecheck` |
| **Run test suite** | `make test` | `.\scripts\dev.ps1 test` |
| **Apply DB migrations** | `make migrate` | `.\scripts\dev.ps1 migrate` |
| **Run all CI checks** | `make check` | `.\scripts\dev.ps1 check` |

---

## 8. Bare-Metal Local Development (Hybrid Workflow)

If you prefer to run services outside Docker (e.g. for rapid breakpoint debugging in an IDE):

### 1. Start Support Infrastructure
```bash
# Keep only PostgreSQL and Redis running in Docker:
docker compose up -d db redis
```

### 2. Run Backend API Locally
```bash
cd apps/api
# Activate venv:
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Run migrations:
alembic upgrade head

# Start FastAPI:
uvicorn app.main:app --reload --port 8000
```

### 3. Run Celery Worker Locally
```bash
cd apps/api
celery -A app.workers.celery_app worker --loglevel=info
```

### 4. Run Frontend Locally
```bash
cd apps/web
npm run dev
# Accessible at http://localhost:5173 (proxies /api to http://localhost:8000)
```

---

## 9. Troubleshooting Guide

### Port 5432 Collision: `FATAL: password authentication failed for user "user"`
- **Cause**: A native PostgreSQL instance is already installed and listening on host port 5432 on your machine.
- **Solution**: The SteamScoop Docker Compose configuration binds `DB_PORT=5433` by default. Ensure your host `.env` uses `DB_PORT=5433` and `DATABASE_URL=postgresql+psycopg://user:password@localhost:5433/steamscoop`. Inside Docker network, services communicate using internal port 5432 at `db:5432`.

### Docker Nginx Healthcheck Timeout
- **Cause**: Alpine Linux `wget` may attempt IPv6 `::1` before IPv4 `127.0.0.1`.
- **Solution**: Nginx is configured to listen on both `80` and `[::]:80`. Healthchecks use `http://127.0.0.1/`.

### Celery Worker Broker Error
- **Cause**: Redis transport version mismatch.
- **Solution**: Celery 5.4+ requires `redis>=6.1.0`. Pinned in `apps/api/pyproject.toml`.

