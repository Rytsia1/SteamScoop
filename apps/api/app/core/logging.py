import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

# Global context variable for request correlation ID
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class CorrelationIdFilter(logging.Filter):
    """Logging filter that injects the current request correlation ID into the log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        cid = correlation_id_ctx.get()
        record.request_id = cid or "-"
        return True


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "source": f"{record.filename}:{record.lineno}",
        }
        if hasattr(record, "request_id") and record.request_id != "-":
            log_data["request_id"] = record.request_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """Configure structured console logging for the application."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(CorrelationIdFilter())

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] [req=%(request_id)s] "
                "%(name)s (%(filename)s:%(lineno)d): %(message)s"
            )
        )

    logging.basicConfig(
        level=numeric_level,
        handlers=[handler],
        force=True,
    )

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
