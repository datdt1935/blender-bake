"""Logging helpers."""

from __future__ import annotations

import logging

LOGGER_NAME = "auto_lowpoly_baker"


def get_logger() -> logging.Logger:
    """Return the extension logger with a stable prefix."""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[Auto Lowpoly Baker] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
