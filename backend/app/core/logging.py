"""Structured logging helpers."""

import json
import logging
from datetime import UTC, datetime

from app.core.context import get_request_context


class JsonFormatter(logging.Formatter):
    """Render log records into a JSON payload with request context."""

    def format(self, record: logging.LogRecord) -> str:
        context = get_request_context()
        payload = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": context.request_id if context is not None else None,
            "trace_id": context.trace_id if context is not None else None,
            "user_id": context.user_id if context is not None else None,
            "path": context.path if context is not None else None,
            "method": context.method if context is not None else None,
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    """Configure application-wide structured logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.handlers = [handler]
