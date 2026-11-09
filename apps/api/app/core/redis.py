import logging

from redis import Redis

from app.core.config import get_settings

logger = logging.getLogger("steamscoop.redis")


def get_redis_client() -> Redis:
    """Provide a configured Redis client instance."""
    settings = get_settings()
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def check_redis_connection(timeout_seconds: float = 3.0) -> bool:
    """Validate active Redis connectivity via PING."""
    try:
        client = get_redis_client()
        return bool(client.ping())
    except Exception as exc:
        logger.warning("Redis connectivity check failed: %s", exc)
        return False
