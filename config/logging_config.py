"""
Logging configuration for the application.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from config.settings import settings


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name
        level: Logging level (defaults to settings.log_level)
        log_file: Optional file path for log output
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level
    log_level = getattr(logging, (level or settings.log_level).upper())
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(settings.log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if settings.log_to_file or log_file:
        file_path = log_file or settings.log_dir / f"{name}.log"
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Default application logger
logger = setup_logger("rag_agent")
