import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime, UTC
from backend.core.request_context import get_request_id

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True

def setup_logging():
    Path("logs").mkdir(exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/app_{timestamp}.log"

    handler = TimedRotatingFileHandler(
        log_file,
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