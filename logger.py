"""
logger.py — Centralized Logging Setup
Smart File Organizer Suite Pro

Provides standardized, thread-safe logging across GUI, CLI, and background services.
"""

import logging
import os
import sys
from typing import Optional

DEFAULT_LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT
) -> logging.Logger:
    """
    Configures the root SmartFileOrganizer logger with console and optional file handlers.

    Args:
        level: logging.DEBUG, logging.INFO, logging.WARNING, or logging.ERROR.
        log_file: Optional absolute path to a log file.
        log_format: Format string for log messages.
        date_format: Date/time format string.

    Returns:
        The configured root logger for the application.
    """
    root_logger = logging.getLogger("SmartFileOrganizer")
    root_logger.setLevel(level)

    # Avoid duplicate handlers on re-configuration
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(log_format, datefmt=date_format)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if log_file:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            formatter = logging.Formatter(log_format, datefmt=date_format)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception:
            pass

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Returns a child logger under the 'SmartFileOrganizer' namespace.

    Args:
        name: Name of the subsystem (e.g. 'Hashing', 'SorterCore', 'Watcher').

    Returns:
        logging.Logger instance.
    """
    if name.startswith("SmartFileOrganizer."):
        return logging.getLogger(name)
    return logging.getLogger(f"SmartFileOrganizer.{name}")
