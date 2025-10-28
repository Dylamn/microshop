import logging
from datetime import UTC, datetime
from typing import Any

import orjson
from pydantic import BaseModel


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured log."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if available
        for key, value in record.__dict__.items():
            if isinstance(value, BaseModel):
                value = value.model_dump()
            if key not in ("args", "msg", "exc_info", "exc_text", "stack_info"):
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return orjson.dumps(log_entry).decode("utf-8")
