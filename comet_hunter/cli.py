import argparse
import os
import signal

from comet_hunter.launcher import (
    start_backend,
    start_frontend
)

from comet_hunter.process_store import (
    save_processes,
    load_processes,
    clear_processes
)


def cmd_start() -> None:

    existing = load_processes()

    if existing:

        print(
            "Comet Hunter already running"
        )

        return

    backend = start_backend()

    frontend = start_frontend()

    save_processes(
        backend.pid,
        frontend.pid
    )

    print(
        "Comet Hunter started"
    )

    print(
        f"Backend PID: {backend.pid}"
    )

    print(
        f"Frontend PID: {frontend.pid}"
    )


def cmd_status() -> None:

    processes = load_processes()

    if not processes:

        print(
            "Comet Hunter not running"
        )

        return

    print(
        f"Backend PID: {processes['backend_pid']}"
    )

    print(
        f"Frontend PID: {processes['frontend_pid']}"
    )


def cmd_stop() -> None:

    processes = load_processes()

    if not processes:

        print(
            "Comet Hunter not running"
        )

        return

    try:

        os.kill(
            processes["backend_pid"],
            signal.SIGTERM
        )

    except Exception:
        pass

    try:

        os.kill(
            processes["frontend_pid"],
            signal.SIGTERM
        )

    except Exception:
        pass

    clear_processes()

    print(
        "Comet Hunter stopped"
    )


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command",
        choices=[
            "start",
            "stop",
            "status"
        ]
    )

    args = parser.parse_args()

    if args.command == "start":
        cmd_start()

    elif args.command == "stop":
        cmd_stop()

    elif args.command == "status":
        cmd_status()