from nicegui import ui
import json
from state.event_store import (
    EVENTS,
    clear_events,
    append_event,
    notify_job_subscribers
)
from styles.theme import PANEL_CARD, PANEL_TITLE, PRIMARY_BUTTON

EVENT_COLORS = {
    "job.running": "text-blue-700",
    "job.completed": "text-green-700",
    "job.failed": "text-red-700",
    "job.cancelled": "text-gray-700",
}

DEFAULT_EVENT_COLOR = "text-purple-700"

event_container: ui.column | None = None

def clear_events_ui() -> None:

    clear_events()
    render_events.refresh()

def handle_job_event(
    event_payload: dict
) -> None:

    append_event(event_payload)
    render_events.refresh()

    notify_job_subscribers(event_payload)

def get_event_color(
    event_name: str
) -> str:

    return EVENT_COLORS.get(
        event_name,
        DEFAULT_EVENT_COLOR
    )


@ui.refreshable
def render_events() -> None:

    if not EVENTS:

        ui.label(
            "No events available"
        ).classes(
            "text-sm text-gray-500 italic"
        )

        return

    for event in reversed(EVENTS):

        event_name = event.get(
            "event",
            "unknown"
        )

        timestamp = event.get(
            "timestamp",
            ""
        )

        if "T" in timestamp:
            timestamp = timestamp.split("T")[1][:8]

        color = get_event_color(
            event_name
        )

        with ui.column().classes(
            """
            w-full
            rounded-lg
            border
            border-gray-200
            bg-gray-50
            p-3
            gap-2
            """
        ):

            with ui.row().classes(
                "w-full items-center justify-between"
            ):

                ui.label(
                    f"[{timestamp}] {event_name}"
                ).classes(
                    f"text-sm font-semibold {color}"
                )

                ui.label(
                    event.get(
                        "job_status",
                        "UNKNOWN"
                    )
                ).classes(
                    """
                    text-xs
                    px-2
                    py-1
                    rounded-full
                    bg-gray-200
                    text-gray-700
                    """
                )

            ui.label(
                event.get(
                    "job_type",
                    "UNKNOWN"
                )
            ).classes(
                "text-xs text-gray-500"
            )

            with ui.expansion(
                "Payload"
            ).classes(
                "w-full"
            ):

                ui.code(
                    json.dumps(
                        event.get("data", {}),
                        indent=2
                    ),
                    language="json"
                ).classes(
                    "w-full text-xs"
                )

def event_stream_panel() -> None:

    with ui.column().classes(f"{PANEL_CARD} h-[760px]"):

        with ui.row().classes("w-full items-center justify-between"):

            ui.label("Event Stream").classes(f"{PANEL_TITLE}")
            ui.button("Clear",on_click=clear_events_ui).classes(f"{PRIMARY_BUTTON}")

        with ui.scroll_area().classes("w-full flex-grow"):
            with ui.column().classes("w-full gap-3"):
                render_events()