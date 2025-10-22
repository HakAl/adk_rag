"""
Logging configuration for the application.
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name
        level: Logging level (defaults to INFO or from settings if available)
        log_file: Optional file path for log output

    Returns:
        Configured logger instance
    """
    # Import settings here to avoid circular import
    try:
        from config.settings import settings
        log_level_str = level or settings.log_level
        log_format = settings.log_format
        should_log_to_file = settings.log_to_file
        log_dir = settings.log_dir
    except ImportError:
        # Fallback if settings not yet loaded
        log_level_str = level or "INFO"
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        should_log_to_file = False
        log_dir = Path("logs")

    logger = logging.getLogger(name)

    # Set level
    log_level = getattr(logging, log_level_str.upper())
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # File handler (if enabled)
    if should_log_to_file or log_file:
        file_path = log_file or log_dir / f"{name}.log"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Default application logger
logger = setup_logger("rag_agent")