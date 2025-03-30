"""
Logging utilities for the monitorpy package.
"""
import logging
import sys
from typing import Optional


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Set up logging for the application.

    Args:
        level: The logging level (default: INFO)
        log_file: Optional file path to log to
    """
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

    # Set requests logging level to WARNING to reduce noise
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger("monitorpy")
    logger.info(f"Logging initialized at level {logging.getLevelName(level)}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the specified name.

    Args:
        name: The logger name

    Returns:
        Logger: Configured logger instance
    """
    return logging.getLogger(f"monitorpy.{name}")
