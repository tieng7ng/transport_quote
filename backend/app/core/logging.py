
import logging
import sys
import json
from datetime import datetime, timezone
from app.core.config import get_settings

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging():
    settings = get_settings()
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level if hasattr(settings, "log_level") else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if settings.debug:
        # Standard format for dev
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        # JSON format for prod
        formatter = JSONFormatter()
    
    handler.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplication
    root_logger.handlers = []
    root_logger.addHandler(handler)
    
    # Set level for libraries
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []
    logging.getLogger("uvicorn").handlers = []
    
    # Propagate uvicorn logs to root
    logging.getLogger("uvicorn").propagate = True
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn.error").propagate = True

    logging.info("Logging initialized")
