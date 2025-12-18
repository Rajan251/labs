import logging
import json
import sys
from typing import Any, Dict
from uuid import uuid4
from contextvars import ContextVar

# Context var to hold request correlation ID
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="unknown")

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "correlation_id": correlation_id_ctx.get(),
            "module": record.module,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "props"):
            log_record.update(record.props)  # type: ignore

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

def setup_logging():
    logger = logging.getLogger("enterprise_app")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    logger.addHandler(handler)
    return logger

logger = setup_logging()
