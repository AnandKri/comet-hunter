import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime, UTC

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

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)