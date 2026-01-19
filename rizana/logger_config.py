# logger_config.py
from datetime import datetime
from pathlib import Path
from sys import stderr
from typing import Any, Dict

from loguru import logger

from rizana.settings import Settings


def filter_record(record: Dict[str, Any]) -> bool:
    """Filters log records based on the file path containing "rizana".

    Args:
        record (dict): The log record to be filtered.

    Returns:
        bool: True if the record is relevant, False otherwise.
    """
    if "rizana" in record["file"].path:
        return True
    return False


def get_log_level(settings: Settings) -> str:
    """Get the appropriate log level based on the environment.

    Args:
        settings: The application settings.

    Returns:
        str: The log level to use.
    """
    env_levels = {
        "development": "DEBUG",
        "testing": "INFO",
        "staging": "INFO",
        "production": "WARNING",
    }
    return env_levels.get(settings.environment.lower(), "INFO")


def configure_logger(settings: Settings) -> None:
    """Configures the logger with enhanced settings.

    This function sets up the logger with:
    - Environment-based log levels
    - Console output with colorized formatting
    - File output with rotation and compression
    - Structured logging format
    - Error tracking
    - Performance monitoring

    Args:
        settings: The application settings.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Define log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Define structured log format for JSON output
    structured_format = (
        '{{"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
        '"level": "{level}", '
        '"name": "{name}", '
        '"function": "{function}", '
        '"line": {line}, '
        '"message": "{message}", '
        '"extra": {extra}}}'
    )

    # Configure logger
    logger.configure(
        handlers=[
            # Console handler
            {
                "sink": stderr,
                "format": log_format,
                "filter": filter_record,
                "backtrace": True,
                "diagnose": True,
                "colorize": True,
            },
            # Main log file handler
            {
                "sink": log_dir / f"rizana_{datetime.now().strftime('%Y%m%d')}.log",
                "format": log_format,
                "filter": filter_record,
                "rotation": "1 day",
                "retention": "30 days",
                "compression": "zip",
                "backtrace": True,
                "diagnose": True,
            },
            # Structured log file handler
            {
                "sink": log_dir / "structured.log",
                "format": structured_format,
                "filter": filter_record,
                "rotation": "1 day",
                "retention": "30 days",
                "compression": "zip",
                "serialize": True,
            },
            # Error file handler
            {
                "sink": log_dir / "error.log",
                "format": log_format,
                "filter": lambda record: record["level"].name == "ERROR",
                "rotation": "1 day",
                "retention": "30 days",
                "compression": "zip",
                "backtrace": True,
                "diagnose": True,
            },
            # Performance log file handler
            {
                "sink": log_dir / "performance.log",
                "format": structured_format,
                "filter": lambda record: "performance" in record["extra"],
                "rotation": "1 day",
                "retention": "30 days",
                "compression": "zip",
                "serialize": True,
            },
        ]
    )

    # Set log level based on environment
    log_level = get_log_level(settings)
    logger.level(log_level)
    logger.info(f"Logger configured with level: {log_level}")

    # Add custom levels for specific use cases
    logger.level("PERFORMANCE", no=25, color="<blue>", icon="⚡")
    logger.level("AUDIT", no=35, color="<yellow>", icon="🔍")
