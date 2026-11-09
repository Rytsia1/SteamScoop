<#
.SYNOPSIS
    SteamScoop Development Management Utility for Windows PowerShell.
.DESCRIPTION
    Provides unified development commands for environment bootstrapping,
    Docker container orchestration, linting, typechecking, testing, and diagnostics.
.EXAMPLE
    .\scripts\dev.ps1 up
    .\scripts\dev.ps1 check
    .\scripts\dev.ps1 validate-env
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("help", "setup", "validate-env", "up", "down", "down-v", "restart", "build", "logs", "ps", "lint", "format", "typecheck", "test", "test-backend", "test-frontend", "migrate", "seed", "check")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot

function Show-Help {
    Write-Host "`nSteamScoop PowerShell Development Utility" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "  .\scripts\dev.ps1 setup        - Initialize .env and install dependencies"
    Write-Host "  .\scripts\dev.ps1 validate-env - Validate environment and dependency reachability"
    Write-Host "  .\scripts\dev.ps1 up           - Start all Docker Compose containers"
    Write-Host "  .\scripts\dev.ps1 down         - Stop Docker Compose containers"
    Write-Host "  .\scripts\dev.ps1 down-v       - Stop containers and wipe volumes (DB/Redis data)"
    Write-Host "  .\scripts\dev.ps1 restart      - Restart containers"
    Write-Host "  .\scripts\dev.ps1 build        - Build container images"
    Write-Host "  .\scripts\dev.ps1 logs         - Follow container logs"
    Write-Host "  .\scripts\dev.ps1 ps           - Check status and health of all containers"
    Write-Host "  .\scripts\dev.ps1 lint         - Run backend (Ruff) and frontend (ESLint) linters"
    Write-Host "  .\scripts\dev.ps1 format       - Format backend code with Ruff"
    Write-Host "  .\scripts\dev.ps1 typecheck    - Run backend (mypy) and frontend (tsc) typechecks"
    Write-Host "  .\scripts\dev.ps1 test         - Run both backend and frontend test suites"
    Write-Host "  .\scripts\dev.ps1 migrate      - Apply Alembic migrations"
    Write-Host "  .\scripts\dev.ps1 seed         - Seed database with development fixtures"
    Write-Host "  .\scripts\dev.ps1 check        - Run all verification checks (lint + typecheck + test)`n"
}

$PyExe = if (Test-Path "$RootDir\apps\api\.venv\Scripts\python.exe") {
    "$RootDir\apps\api\.venv\Scripts\python.exe"
} else {
    "python"
}

$RuffExe = if (Test-Path "$RootDir\apps\api\.venv\Scripts\ruff.exe") {
    "$RootDir\apps\api\.venv\Scripts\ruff.exe"
} else {
    "ruff"
}

$MypyExe = if (Test-Path "$RootDir\apps\api\.venv\Scripts\mypy.exe") {
    "$RootDir\apps\api\.venv\Scripts\mypy.exe"
} else {
    "mypy"
}

$PytestExe = if (Test-Path "$RootDir\apps\api\.venv\Scripts\pytest.exe") {
    "$RootDir\apps\api\.venv\Scripts\pytest.exe"
} else {
    "pytest"
}

$AlembicExe = if (Test-Path "$RootDir\apps\api\.venv\Scripts\alembic.exe") {
    "$RootDir\apps\api\.venv\Scripts\alembic.exe"
} else {
    "alembic"
}

switch ($Command) {
    "help" {
        Show-Help
    }
    "setup" {
        Write-Host "==> Checking .env configuration..." -ForegroundColor Yellow
        if (-not (Test-Path "$RootDir\.env")) {
            Copy-Item "$RootDir\.env.example" "$RootDir\.env"
            Write-Host "Created .env from .env.example" -ForegroundColor Green
        } else {
            Write-Host ".env already exists." -ForegroundColor Gray
        }

        Write-Host "==> Installing frontend dependencies..." -ForegroundColor Yellow
        npm --prefix "$RootDir\apps\web" install

        Write-Host "==> Installing backend dependencies..." -ForegroundColor Yellow
        if (-not (Test-Path "$RootDir\apps\api\.venv")) {
            if (Get-Command "uv" -ErrorAction SilentlyContinue) {
                uv venv "$RootDir\apps\api\.venv" --python 3.11
                uv pip install --python "$RootDir\apps\api\.venv\Scripts\python.exe" -e "$RootDir\apps\api[dev]"
            } else {
                python -m venv "$RootDir\apps\api\.venv"
                & "$RootDir\apps\api\.venv\Scripts\pip.exe" install --upgrade pip
                & "$RootDir\apps\api\.venv\Scripts\pip.exe" install -e "$RootDir\apps\api[dev]"
            }
        }
        Write-Host "Setup complete!" -ForegroundColor Green
    }
    "validate-env" {
        & $PyExe "$RootDir\scripts\validate_env.py"
    }
    "up" {
        docker compose up -d
    }
    "down" {
        docker compose down
    }
    "down-v" {
        docker compose down -v
    }
    "restart" {
        docker compose restart
    }
    "build" {
        docker compose build
    }
    "logs" {
        docker compose logs -f
    }
    "ps" {
        docker compose ps
    }
    "lint" {
        Write-Host "==> Linting backend (Ruff)..." -ForegroundColor Yellow
        & $RuffExe check "$RootDir\apps\api"
        Write-Host "==> Linting frontend (ESLint)..." -ForegroundColor Yellow
        npm --prefix "$RootDir\apps\web" run lint
    }
    "format" {
        Write-Host "==> Formatting backend (Ruff)..." -ForegroundColor Yellow
        & $RuffExe format "$RootDir\apps\api"
    }
    "typecheck" {
        Write-Host "==> Typechecking backend (Mypy)..." -ForegroundColor Yellow
        & $MypyExe --config-file "$RootDir\apps\api\pyproject.toml" "$RootDir\apps\api\app"
        Write-Host "==> Typechecking frontend (TypeScript tsc)..." -ForegroundColor Yellow
        npm --prefix "$RootDir\apps\web" run typecheck
    }
    "test-backend" {
        Write-Host "==> Running backend Pytest..." -ForegroundColor Yellow
        & $PytestExe -c "$RootDir\apps\api\pyproject.toml" "$RootDir\apps\api\tests"
    }
    "test-frontend" {
        Write-Host "==> Running frontend Vitest..." -ForegroundColor Yellow
        npm --prefix "$RootDir\apps\web" run test
    }
    "test" {
        & $PSScriptRoot\dev.ps1 test-backend
        & $PSScriptRoot\dev.ps1 test-frontend
    }
    "migrate" {
        Write-Host "==> Applying Alembic migrations..." -ForegroundColor Yellow
        & $AlembicExe -c "$RootDir\apps\api\alembic.ini" upgrade head
    }
    "seed" {
        Write-Host "==> Seeding database with development fixtures..." -ForegroundColor Yellow
        & $PyExe "$RootDir\apps\api\scripts\seed_dev_data.py"
    }
    "check" {
        Write-Host "`n=== 1. LINTING ===" -ForegroundColor Cyan
        & $PSScriptRoot\dev.ps1 lint
        Write-Host "`n=== 2. TYPE CHECKING ===" -ForegroundColor Cyan
        & $PSScriptRoot\dev.ps1 typecheck
        Write-Host "`n=== 3. TESTS ===" -ForegroundColor Cyan
        & $PSScriptRoot\dev.ps1 test
        Write-Host "`n=== ALL VERIFICATION CHECKS PASSED ===" -ForegroundColor Green
    }
}

