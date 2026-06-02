from typing import Callable
from config import MAX_EVENTS

EVENTS: list[dict] = []

job_event_subscribers: list[Callable[[dict], None]] = []

def subscribe_to_job_events(
    callback: Callable[[dict], None]
) -> None:

    job_event_subscribers.append(callback)


def notify_job_subscribers(
    event_payload: dict
) -> None:

    for callback in job_event_subscribers:
        callback(event_payload)
    

def append_event(
    event_payload: dict
) -> None:

    EVENTS.append(event_payload)
    if len(EVENTS) > MAX_EVENTS:
        EVENTS.pop(0)

def clear_events() -> None:

    EVENTS.clear()