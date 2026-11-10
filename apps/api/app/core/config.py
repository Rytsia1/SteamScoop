import json
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application environment
    APP_NAME: str = "SteamScoop API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "testing", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] | str = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return [str(item) for item in v]
        return []

    # Database configuration (PostgreSQL)
    DATABASE_URL: str = "postgresql+psycopg://user:password@localhost:5432/steamscoop"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Cache & Message Broker (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Steam API Configuration
    STEAM_API_KEY: str | None = None
    STEAM_API_TIMEOUT_SECONDS: int = 15
    STEAM_API_MAX_RETRIES: int = 3

    # Security (for future authentication milestones)
    SECRET_KEY: str = "development-secret-key-do-not-use-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Data Exports Configuration
    EXPORT_STORAGE_PATH: str = "storage/exports"
    EXPORT_DEFAULT_TTL_DAYS: int = 7
    EXPORT_MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    EXPORT_MAX_ACTIVE_PER_USER: int = 3
    EXPORT_DEFAULT_ROW_LIMIT: int = 10000
    EXPORT_RESEARCHER_ROW_LIMIT: int = 50000
    EXPORT_ADMIN_ROW_LIMIT: int = 100000


@lru_cache
def get_settings() -> Settings:
    return Settings()
