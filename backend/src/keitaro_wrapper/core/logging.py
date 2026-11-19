from __future__ import annotations

import logging
from logging.config import dictConfig

from keitaro_wrapper.core.config import Settings


def configure_logging(settings: Settings) -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {
                "level": settings.log_level.upper(),
                "handlers": ["console"],
            },
            "loggers": {
                "uvicorn.access": {"level": "WARNING", "propagate": True},
                "httpx": {"level": "WARNING", "propagate": True},
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
