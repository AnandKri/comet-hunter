from pathlib import Path
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent

BACKEND_MODULE = "backend.main"
FRONTEND_SCRIPT = ROOT_DIR / "frontend" / "app.py"


def start_backend() -> subprocess.Popen:

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000"
        ],
        cwd=ROOT_DIR
    )


def start_frontend() -> subprocess.Popen:

    return subprocess.Popen(
        [sys.executable, str(FRONTEND_SCRIPT)],
        cwd=ROOT_DIR
    )