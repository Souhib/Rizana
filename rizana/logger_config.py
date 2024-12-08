# logger_config.py
from sys import stderr

from loguru import logger


def filter_record(record):
    """
    Filters log records based on the file path containing "rizana".

    This function checks if the file path of the log record contains the string "rizana".
    If it does, the record is considered relevant and the function returns True. Otherwise,
    it returns False.

    Args:
        record (dict): The log record to be filtered.

    Returns:
        bool: True if the record is relevant, False otherwise.
    """
    if "rizana" in record["file"].path:
        return True
    return False


def configure_logger():
    """
    Configures the logger to filter records based on file path and output to stderr.

    This function sets up the logger to output logs to stderr and applies a filter to
    only include records where the file path contains "rizana". It also disables backtrace
    logging.
    """
    logger.configure(
        handlers=[{"sink": stderr, "filter": filter_record, "backtrace": False}]
    )
