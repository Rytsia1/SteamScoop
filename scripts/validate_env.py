#!/usr/bin/env python3
"""SteamScoop Environment and Dependency Validation Script.

Validates that environment configuration, database reachability,
and cache/broker connections are properly initialized.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add apps/api to sys.path so app packages can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = ROOT_DIR / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


def mask_secret(value: str | None, visible_chars: int = 4) -> str:
    """Mask sensitive string values for display."""
    if not value:
        return "<not set>"
    if len(value) <= visible_chars * 2:
        return "***"
    return f"{value[:visible_chars]}...{value[-visible_chars:]}"


def main() -> int:
    print("=" * 70)
    print(" SteamScoop Environment & Dependency Diagnostic Validation")
    print("=" * 70)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Check .env file
    env_file = ROOT_DIR / ".env"
    if not env_file.exists():
        errors.append(
            f"Missing .env file at {env_file}. Copy from .env.example: 'cp .env.example .env'"
        )
        print(f"[-] .env file: MISSING ({env_file})")
    else:
        print(f"[+] .env file: FOUND ({env_file})")

    # 2. Load Settings
    try:
        from app.core.config import get_settings

        settings = get_settings()
        print(f"[+] Settings Model: Successfully parsed via Pydantic Settings")
        print(f"    - APP_NAME: {settings.APP_NAME}")
        print(f"    - APP_VERSION: {settings.APP_VERSION}")
        print(f"    - APP_ENV: {settings.APP_ENV}")
        print(f"    - DEBUG: {settings.DEBUG}")
        print(f"    - CORS_ORIGINS: {settings.CORS_ORIGINS}")
    except Exception as exc:
        errors.append(f"Failed to parse settings: {exc}")
        print(f"[-] Settings Model: FAILED ({exc})")
        return 1

    # Production safety checks
    if settings.APP_ENV == "production":
        if settings.DEBUG:
            errors.append("DEBUG must be False in production environment.")
        if "development" in settings.SECRET_KEY.lower():
            errors.append("SECRET_KEY must be a cryptographically secure random string in production.")
    else:
        if "development" in settings.SECRET_KEY.lower():
            warnings.append("Using default development SECRET_KEY (acceptable for local dev).")

    # 3. Database Connectivity Check
    print("\n--- Subsystem Connectivity Probes ---")
    try:
        from app.db.session import check_database_connection

        db_ok = check_database_connection(timeout_seconds=3.0)
        if db_ok:
            print(f"[+] PostgreSQL Database: CONNECTED ({settings.DATABASE_URL.split('@')[-1]})")
        else:
            errors.append(
                f"Cannot connect to PostgreSQL at {settings.DATABASE_URL.split('@')[-1]}. "
                "Ensure container 'steamscoop-db' is healthy or local database is running."
            )
            print(f"[-] PostgreSQL Database: UNREACHABLE ({settings.DATABASE_URL.split('@')[-1]})")
    except Exception as exc:
        errors.append(f"Database probe error: {exc}")
        print(f"[-] PostgreSQL Database: ERROR ({exc})")

    # 4. Redis Connectivity Check
    try:
        from app.core.redis import check_redis_connection

        redis_ok = check_redis_connection(timeout_seconds=3.0)
        if redis_ok:
            print(f"[+] Redis Broker & Cache: CONNECTED ({settings.REDIS_URL})")
        else:
            errors.append(
                f"Cannot connect to Redis at {settings.REDIS_URL}. "
                "Ensure container 'steamscoop-redis' is running."
            )
            print(f"[-] Redis Broker & Cache: UNREACHABLE ({settings.REDIS_URL})")
    except Exception as exc:
        errors.append(f"Redis probe error: {exc}")
        print(f"[-] Redis Broker & Cache: ERROR ({exc})")

    # 5. Frontend Environment Template Check
    web_env_example = ROOT_DIR / "apps" / "web" / ".env.example"
    if web_env_example.exists():
        print(f"[+] Frontend Environment: Template present ({web_env_example.name})")
    else:
        warnings.append("Missing apps/web/.env.example template.")
        print(f"[!] Frontend Environment: Missing {web_env_example}")

    # Summary
    print("\n" + "=" * 70)
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"  [!] {warn}")

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  [-] {err}")
        print("\nResult: VALIDATION FAILED - Address the errors above.")
        return 1

    print("Result: ALL CHECKS PASSED - Development environment is healthy.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())

