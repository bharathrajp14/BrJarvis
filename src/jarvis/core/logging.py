"""Central logging configuration owned by the rebuilt core."""

from __future__ import annotations

import logging as stdlib_logging
import sys

_CONFIGURED = False


def configure_logging(level: str = "INFO", *, force: bool = False) -> None:
    """Configure one concise stderr handler without touching application secrets."""
    global _CONFIGURED
    if _CONFIGURED and not force:
        return
    normalized = level.strip().upper()
    numeric_level = getattr(stdlib_logging, normalized, stdlib_logging.INFO)
    handler = stdlib_logging.StreamHandler(sys.stderr)
    handler.setFormatter(stdlib_logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = stdlib_logging.getLogger()
    if force:
        root.handlers.clear()
    root.setLevel(numeric_level)
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> stdlib_logging.Logger:
    """Return a logger under the canonical runtime namespace."""
    return stdlib_logging.getLogger(f"jarvis.{name}")
