import requests
from typing import Any
from config import SERVER_BASE_URL, REQUEST_TIMEOUT

def health_check() -> bool:
    """
    Check backend health status.

    Calls the `/health` endpoint and returns whether
    the backend reports itself as healthy.

    :return: True if backend is healthy, otherwise False
    """

    try:
        response = requests.get(
            f"{SERVER_BASE_URL}/health",
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        payload: dict[str, Any] = response.json()

        return payload["data"]["status"] == "healthy"

    except Exception:
        return False


def get_active_slot() -> dict[str, Any] | None:
    """
    Fetch currently active slot.

    :return:
        Slot response dictionary if available,
        otherwise None.
    """

    try:
        response = requests.get(
            f"{SERVER_BASE_URL}/slots/active",
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        payload: dict[str, Any] = response.json()

        return payload.get("data")

    except Exception:
        return None


def get_next_active_slot() -> dict[str, Any] | None:
    """
    Fetch next upcoming slot.

    :return:
        Slot response dictionary if available,
        otherwise None.
    """

    try:
        response = requests.get(
            f"{SERVER_BASE_URL}/slots/next-active",
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        payload: dict[str, Any] = response.json()

        return payload.get("data")

    except Exception:
        return None


def sync_slots() -> dict[str, Any] | None:
    """
    Trigger slot synchronization.

    :return:
        Sync response dictionary if successful,
        otherwise None.
    """

    try:
        response = requests.post(
            f"{SERVER_BASE_URL}/slots/sync",
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        payload: dict[str, Any] = response.json()

        return payload.get("data")

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