"""
Logging utilities for the application.

This module provides a simple logging setup for debugging and audit purposes.
"""

import logging
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "OPCUACertManager",
    log_level: int = logging.INFO,
    log_file: Path | None = None,
) -> logging.Logger:
    """
    Set up and return a logger instance.
    
    Args:
        name: Logger name.
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to log file. If None, logs to console only.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Default logger instance
default_logger = setup_logger()