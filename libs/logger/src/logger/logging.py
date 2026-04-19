import logging
import json
import os
import sys
from datetime import datetime, timezone

ENV = os.getenv("ENVIRONMENT", "development")
SERVICE = os.getenv("SERVICE_NAME", "transition-watch")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)

class DevFormatter(logging.Formatter):
    def format(self, record):
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        return f"{ts} | {record.levelname:<8} | {record.name} - {record.getMessage()}"

def configure_logging(level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(DevFormatter() if ENV == "development" else JSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

def get_logger(name: str):
    return logging.getLogger(name)
