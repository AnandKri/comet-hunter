from collections.abc import Callable

from models.processed_file import ProcessedFile


frames: list[ProcessedFile] = []

current_index: int = 0

_subscribers: list[Callable[[], None]] = []


def subscribe_to_frame_updates(
    callback: Callable[[], None]
) -> None:

    _subscribers.append(
        callback
    )


def notify_frame_subscribers() -> None:

    for callback in _subscribers:
        callback()


def set_frames(
    new_frames: list[ProcessedFile]
) -> None:

    global frames
    global current_index

    frames = new_frames
    current_index = 0

    notify_frame_subscribers()


def current_frame() -> ProcessedFile | None:

    if not frames:
        return None

    return frames[current_index]


def next_frame() -> None:

    global current_index

    if not frames:
        return

    current_index = min(
        current_index + 1,
        len(frames) - 1
    )

    notify_frame_subscribers()


def previous_frame() -> None:

    global current_index

    if not frames:
        return

    current_index = max(
        current_index - 1,
        0
    )

    notify_frame_subscribers()


def total_frames() -> int:

    return len(frames)


def current_position() -> int:

    return current_index + 1