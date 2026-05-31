import requests
from typing import Any
from config import SERVER_BASE_URL, REQUEST_TIMEOUT
from models.slot import Slot
from models.job import JobQueued
from models.processed_file import ProcessedFile

def health_check() -> bool:
    """
    Check backend health status.

    Calls the `/health` endpoint and returns whether
    the backend reports itself as healthy.

    :return: True if backend is healthy, otherwise False
    """

    try:
        payload = _get("/health")
        return payload["data"]["status"] == "healthy"

    except Exception:
        return False

def get_active_slot() -> Slot | None:
    """
    Fetch currently active slot.

    :return:
        Slot response dictionary if available,
        otherwise None.
    """

    try:
        payload = _get("/slots/active")
        data = payload["data"]

        return Slot(
            start=data["start"],
            end=data["end"]
        )

    except Exception:
        return None

def get_next_active_slot() -> Slot | None:
    """
    Fetch next upcoming slot.

    :return:
        Slot response dictionary if available,
        otherwise None.
    """

    try:
        payload = _get("/slots/next-active")
        data = payload["data"]
        
        return Slot(
            start=data["start"],
            end=data["end"]
        )

    except Exception:
        return None

def sync_slots() -> JobQueued | None:
    """
    Trigger slot synchronization.

    :return:
        Sync response dictionary if successful,
        otherwise None.
    """

    try:
        payload = _post("/slots/sync")
        data = payload["data"]

        return JobQueued(
            job_id=data["job_id"],
            existing=data["existing"],
            status=data["status"]
        )

    except Exception:
        return None

def get_job_status(job_id: str) -> dict[str, Any] | None:
    """
    Fetch background job status.

    :param job_id:
        Background job identifier.

    :return:
        Job response dictionary if available,
        otherwise None.
    """

    try:
        response = requests.get(
            f"{SERVER_BASE_URL}/jobs/{job_id}",
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        payload: dict[str, Any] = response.json()

        return payload.get("data")

    except Exception:
        return None

def build_job_events_url(
    job_id: str
) -> str:
    """
    Returns SSE endpoint URL for a job stream.

    :param job_id:
        Background job identifier.

    :return:
        Absolute SSE endpoint URL.
    """

    return f"{SERVER_BASE_URL}/jobs/{job_id}/events"

def start_scheduler(
    instruments: list[str]
) -> JobQueued | None:

    try:

        payload = _post(
            "/scheduler/start",
            params={
                "instruments": instruments
            }
        )

        data = payload["data"]

        return JobQueued(
            job_id=data["job_id"],
            existing=data.get(
                "existing",
                False
            ),
            status=data.get(
                "status",
                "QUEUED"
            )
        )

    except Exception:
        return None

def cancel_job(
    job_id: str
) -> bool:

    try:

        payload = _post(
            f"/jobs/{job_id}/cancel"
        )

        return payload is not None

    except Exception:
        return False

def sync_frames(
    instrument: str,
    start: str,
    end: str
) -> JobQueued | None:

    try:

        payload = _post(
            "/frames/sync",
            params={
                "instrument": instrument,
                "start": start,
                "end": end
            }
        )

        data = payload["data"]

        return JobQueued(
            job_id=data["job_id"],
            existing=data["existing"],
            status=data["status"]
        )

    except Exception:
        return None

def get_frames(
    instrument: str,
    start: str,
    end: str,
    limit: int = 100,
    offset: int = 0
) -> list[ProcessedFile] | None:

    try:

        payload = _get(
            "/frames",
            params={
                "instrument": instrument,
                "start": start,
                "end": end,
                "limit": limit,
                "offset": offset
            }
        )

        data = payload["data"]

        return [
            ProcessedFile(
                processed_file_name=file["processed_file_name"],
                instrument=file["instrument"],
                processed_file_url=file["processed_file_url"],
                datetime_of_observation=file["datetime_of_observation"]
            )
            for file in data["files"]
        ]

    except Exception:

        return None

def _get(
    endpoint: str,
    params: dict[str, Any] | None = None
) -> dict[str, Any] | None:

    try:

        response = requests.get(
            f"{SERVER_BASE_URL}{endpoint}",
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return response.json()

    except Exception:
        return None
    
def _post(
    endpoint: str,
    params: dict[str, Any] | None = None
) -> dict[str, Any] | None:

    try:

        response = requests.post(
            f"{SERVER_BASE_URL}{endpoint}",
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return response.json()

    except Exception:
        return None