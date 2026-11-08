"""
VEDANTA — Structured Logging Configuration
Uses structlog for consistent, machine-parseable logs.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from app.core.config import settings


def add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add VEDANTA application context to every log entry."""
    event_dict["app"] = "vedanta"
    event_dict["version"] = settings.app_version
    event_dict["env"] = settings.app_env
    return event_dict


def add_logger_name(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Safely extract logger name if present on logger or in context."""
    if hasattr(logger, "name"):
        event_dict["logger"] = logger.name
    return event_dict


def configure_logging() -> None:
    """Configure structlog and standard logging."""
    log_level = getattr(logging, settings.app_log_level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.is_development:
        # Pretty console output in development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON output in production
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging so SQLAlchemy, uvicorn, etc. use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str = "vedanta") -> structlog.BoundLogger:
    """Get a named structlog logger."""
    return structlog.get_logger().bind(logger=name)
