import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime, UTC
from backend.core.request_context import get_request_id
from backend.core.storage import LOG_DIR

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True

def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"app_{timestamp}.log"

    handler = TimedRotatingFileHandler(
        str(log_file),
        when="midnight",
        backupCount=7,
        encoding="utf-8"
    )

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s | %(message)s")
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)