from pathlib import Path

APP_HOME = Path.home() / ".comet_hunter"
RAW_DIR = APP_HOME / "data" / "raw"
PROCESSED_DIR = APP_HOME / "data" / "processed"
LOG_DIR = APP_HOME / "logs"
DB_PATH = APP_HOME / "comet_hunter.db"

def ensure_application_directories() -> None:
    APP_HOME.mkdir(parents=True, exist_ok=True)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    LOG_DIR.mkdir(parents=True, exist_ok=True)