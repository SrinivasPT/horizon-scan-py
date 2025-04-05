import logging
import logging.config
import os
import sys
from typing import Dict, Optional

# Default configuration
DEFAULT_LOG_LEVEL = "INFO"  # Changed to INFO for project-wide default
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Dictionary to store specific logger configurations
_logger_levels: Dict[str, int] = {}


# Configure the root logger with basic config
def configure_logging(log_level: Optional[str] = None):
    """
    Configure logging for the entire application.

    Args:
        log_level: Optional override for log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Determine log level from environment or use default
    level = log_level or os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL)

    # Convert string log level to logging constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {level}. Using default: {DEFAULT_LOG_LEVEL}")
        numeric_level = getattr(logging, DEFAULT_LOG_LEVEL)

    # Configure the root logger
    logging.basicConfig(level=numeric_level, format=DEFAULT_LOG_FORMAT, handlers=[logging.StreamHandler(sys.stdout)])

    # Set level for specific loggers if needed
    # For example, to reduce verbosity of some libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Log the configuration
    logging.info(f"Logging configured with level: {level}")


# Get a logger for a specific module with optional custom level
def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger for the specified module name with an optional custom log level.

    Args:
        name: The module name (typically __name__)
        level: Optional custom log level for this specific logger
               (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # If a custom level is specified for this logger
    if level:
        numeric_level = getattr(logging, level.upper(), None)
        if isinstance(numeric_level, int):
            logger.setLevel(numeric_level)
            # Store the level for potential resets
            _logger_levels[name] = numeric_level

    return logger


# Set/change the log level for a specific logger
def set_log_level(name: str, level: str) -> None:
    """
    Set or change the log level for a specific named logger.

    Args:
        name: The logger name
        level: Log level to set (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), None)

    if isinstance(numeric_level, int):
        logger.setLevel(numeric_level)
        _logger_levels[name] = numeric_level
        logging.debug(f"Log level for {name} set to {level}")
    else:
        logging.error(f"Invalid log level: {level} for logger {name}")


# Initialize logging with default configuration
configure_logging()
