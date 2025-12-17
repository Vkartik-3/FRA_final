#!/usr/bin/env python3
"""
Logging configuration for FRA pipeline.

Provides simple logging setup with both console and file output.
"""

import logging
from pathlib import Path
from datetime import datetime


def setup_logger(name, log_dir="logs", level=logging.INFO):
    """
    Set up a logger with both file and console handlers.

    Args:
        name: Logger name (usually script name)
        log_dir: Directory to store log files (relative to fra_pipeline/)
        level: Logging level

    Returns:
        Configured logger
    """
    # Create logs directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    log_path = base_dir / log_dir
    log_path.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Create formatters
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )

    # File handler (with timestamp)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = log_path / f"{name}_{timestamp}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console handler (less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging to: {log_file}")

    return logger


if __name__ == "__main__":
    # Test the logger
    logger = setup_logger('test')
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")
    logger.debug("This is a debug message (only in file)")
