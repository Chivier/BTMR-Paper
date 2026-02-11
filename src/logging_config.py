"""
Logging configuration for BTMR with full backtrace support.

Sets up comprehensive logging with backtrace information for debugging.
"""
import os
import sys
from pathlib import Path
from loguru import logger

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Output directory
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def setup_logging():
    """Configure comprehensive logging with backtrace support."""
    # Remove default handler
    logger.remove()
    
    # Add console handler with backtrace
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="INFO",
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler with backtrace and detailed formatting
    logger.add(
        OUTPUT_DIR / "app.log",
        rotation="10 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        enqueue=False  # Disable enqueue for immediate writes during development
    )
    
    # Add separate error log for exceptions with full backtrace
    logger.add(
        OUTPUT_DIR / "errors.log",
        rotation="5 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        backtrace=True,
        diagnose=True,
        enqueue=False  # Disable enqueue for immediate writes during development
    )
    
    logger.info("Logging configuration initialized with backtrace support")

# Logging configuration - call setup_logging() to initialize
