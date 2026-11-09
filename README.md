# SteamScoop

SteamScoop is an intelligence and analytics platform for Steam games. It processes player reviews using sentiment analysis, aspect-based sentiment analysis (ABSA), and topic modeling to deliver actionable product insights for developers, publishers, and players.

---

## 🏗️ Architecture & Monorepo Structure

SteamScoop is organized as a clean monorepo:

```text
steamscoop/
├── .github/
│   └── workflows/          # GitHub Actions CI pipelines
├── apps/
│   ├── api/                # FastAPI backend & Celery ingestion workers
│   │   ├── alembic/        # Database migration revisions
│   │   ├── app/            # Application code (API, Core, DB, Models, Repositories, Services)
│   │   └── tests/          # Pytest suite (unit, integration, contract)
│   └── web/                # React 18 + TypeScript + Vite SPA
│       ├── src/            # Components, hooks, lib, pages, styles, types
│       └── tests/          # Vitest suite with React Testing Library
├── Docs/                   # Authoritative engineering documentation
├── infra/                  # Infrastructure configurations & scripts
├── ml/                     # ML pipelines, datasets, experiments & models
├── docker-compose.yml      # Multi-container orchestration (DB, Redis, API, Worker, Beat, Web)
└── .env.example            # Environment configuration template
```

---

## 💻 Tech Stack Baseline

| Domain | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript (`strict: true`), Vite, Tailwind CSS, TanStack Query, Apache ECharts, Lucide React, Vitest |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, psycopg v3, Celery, Redis, pytest |
| **Data & Cache** | PostgreSQL 15, Redis 7 |
| **Tooling & CI** | Docker, Docker Compose, GitHub Actions, Ruff, mypy, ESLint |

---

## 🚀 Quick Start with Docker Compose

The fastest way to spin up the entire SteamScoop ecosystem locally:

### 1. Configure Environment
```bash
# Copy template environment variables
cp .env.example .env
```

### 2. Build and Start Services
```bash
# Using Make (Linux/macOS):
make up

# Using PowerShell (Windows):
.\scripts\dev.ps1 up

# Direct Docker Compose:
docker compose up -d --build
```

### 3. Validate Environment & Connectivity
Run the diagnostic validator to ensure database and Redis reachability:
```bash
python scripts/validate_env.py
```

### 4. Verify Health & Connectivity
- **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Web Frontend**: [http://localhost:3000](http://localhost:3000)

### 5. Stop Services
```bash
# Using Make:
make down
# Or using PowerShell:
.\scripts\dev.ps1 down

# Wipe named volumes (Postgres & Redis data):
make down-v
```

---

## ⚡ Unified Development Commands

SteamScoop provides consistent developer commands via `Makefile` (Linux/macOS) and `.\scripts\dev.ps1` (Windows):

| Action | Linux/macOS (`make`) | Windows (`.\scripts\dev.ps1`) |
| :--- | :--- | :--- |
| **Setup dev environment** | `make dev-setup` | `.\scripts\dev.ps1 setup` |
| **Run diagnostics** | `make validate-env` | `.\scripts\dev.ps1 validate-env` |
| **Start stack** | `make up` | `.\scripts\dev.ps1 up` |
| **Stop stack** | `make down` | `.\scripts\dev.ps1 down` |
| **Check containers** | `make ps` | `.\scripts\dev.ps1 ps` |
| **Stream logs** | `make logs` | `.\scripts\dev.ps1 logs` |
| **Run linters** | `make lint` | `.\scripts\dev.ps1 lint` |
| **Format code** | `make format` | `.\scripts\dev.ps1 format` |
| **Typecheck** | `make typecheck` | `.\scripts\dev.ps1 typecheck` |
| **Run tests** | `make test` | `.\scripts\dev.ps1 test` |
| **Apply migrations** | `make migrate` | `.\scripts\dev.ps1 migrate` |
| **Run full CI verification** | `make check` | `.\scripts\dev.ps1 check` |

---

## 🛠️ Local Development (Bare-Metal)

### Prerequisites
- Python 3.11+ (or `uv`)
- Node.js 20+ & npm 10+
- Running PostgreSQL 15+ and Redis 7+ instances

---

### Backend Service (`apps/api`)

```bash
cd apps/api

# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies (including dev tools)
pip install -e ".[dev]"

# 3. Run database migrations
alembic upgrade head

# 4. Start the FastAPI development server
uvicorn app.main:app --reload --port 8000

# 5. Start Celery worker (in separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# 6. Start Celery beat scheduler (optional, for cron jobs)
celery -A app.workers.celery_app beat --loglevel=info
```

#### Run Backend Checks:
```bash
cd apps/api
ruff check .           # Linting
ruff format --check .  # Format check
mypy app               # Strict type checking
pytest                 # Test suite
```

---

### Frontend Application (`apps/web`)

```bash
cd apps/web

# 1. Install dependencies
npm install

# 2. Start Vite development server
npm run dev
# Accessible at http://localhost:5173
```

#### Run Frontend Checks:
```bash
cd apps/web
npm run lint           # ESLint
npm run typecheck      # TypeScript compilation check
npm run test           # Vitest unit tests
npm run build          # Production build check
```

---

## 📡 API Response Specification

All REST endpoints adhere to the standardized response envelope defined in `Docs/API_SPECIFICATION.md`:

```json
{
  "data": {
    "status": "healthy",
    "version": "0.1.0",
    "environment": "development"
  },
  "error": null,
  "meta": {
    "request_id": "018e6e5f-1e82-7d0b-b159-f2db8db10a84",
    "timestamp": "2026-11-09T13:20:00Z"
  }
}
```

---

## 📚 Engineering Documentation Reference

Detailed architectural and operational specifications reside in `Docs/`:
- `Docs/DEVELOPMENT.md` — Comprehensive Local Development & Troubleshooting Guide
- `CONTRIBUTING.md` — Contribution Process, Branching & Commit Conventions
- `Docs/SRS.md` — Software Requirements Specification
- `Docs/SYSTEM_DESIGN.md` — System Architecture & Data Flows
- `Docs/DATABASE_DESIGN.md` — Database Schema, Partitioning & Relational Integrity
- `Docs/API_SPECIFICATION.md` — REST API Endpoints & Contract Envelopes
- `Docs/ML_SPECIFICATION.md` — Model Architecture & Sentiment Analysis Pipelines
- `Docs/CODING_STANDARDS.md` — Monorepo Architecture & Coding Standards
- `Docs/TESTING_STRATEGY.md` — Testing Tiers & Evaluation Metrics
- `Docs/IMPLEMENTATION_ROADMAP.md` — Sprint Milestones & Delivery Schedule

