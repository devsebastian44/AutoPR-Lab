"""
AutoPR Lab - Logger
=====================
Sistema de logging centralizado con formato consistente y colores.
"""

import logging
import os
import sys

# Colores ANSI para terminal
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GRAY = "\033[90m"


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para output de terminal."""

    LEVEL_COLORS = {
        logging.DEBUG: GRAY,
        logging.INFO: CYAN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: f"{BOLD}{RED}",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, RESET)
        level_str = f"{color}{record.levelname:8}{RESET}"
        name_str = f"{BLUE}{record.name}{RESET}"
        return f"{level_str} {name_str} | {record.getMessage()}"


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """
    Obtiene un logger configurado para AutoPR Lab.

    Args:
        name: Nombre del módulo (ej: "scanner", "github_api")
        level: Nivel de logging (default: INFO, o DEBUG si LOG_LEVEL=DEBUG)
    """
    logger = logging.getLogger(f"autopr.{name}")

    if logger.handlers:
        return logger

    if level is None:
        env_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger
