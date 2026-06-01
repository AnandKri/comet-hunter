from pathlib import Path
import json

PROCESS_FILE = (
    Path.home()
    / ".comet_hunter_processes.json"
)

def save_processes(
    backend_pid: int,
    frontend_pid: int
) -> None:

    PROCESS_FILE.write_text(
        json.dumps(
            {
                "backend_pid": backend_pid,
                "frontend_pid": frontend_pid
            }
        )
    )

def load_processes() -> dict | None:

    if not PROCESS_FILE.exists():
        return None

    return json.loads(
        PROCESS_FILE.read_text()
    )

def clear_processes() -> None:

    if PROCESS_FILE.exists():
        PROCESS_FILE.unlink()