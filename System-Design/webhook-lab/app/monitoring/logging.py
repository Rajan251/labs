"""
Structured logging configuration.
"""
import logging
import sys
from pythonjsonlogger import jsonlogger

from app.config import settings


def setup_logging():
    """Configure structured JSON logging."""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        timestamp=True
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Initialize logger
logger = setup_logging()
