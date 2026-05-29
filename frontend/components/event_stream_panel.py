from nicegui import ui
from typing import Callable
from services.api import get_job_events_url
import json

MAX_EVENTS = 50

EVENTS: list[dict] = []

EVENT_COLORS = {
    "job.running": "text-blue-700",
    "job.completed": "text-green-700",
    "job.failed": "text-red-700",
    "job.cancelled": "text-gray-700",
}

DEFAULT_EVENT_COLOR = "text-purple-700"

event_container: ui.column | None = None

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


def get_event_color(
    event_name: str
) -> str:

    return EVENT_COLORS.get(
        event_name,
        DEFAULT_EVENT_COLOR
    )


def append_event(
    event_payload: dict
) -> None:

    EVENTS.append(event_payload)

    if len(EVENTS) > MAX_EVENTS:
        EVENTS.pop(0)

    render_events.refresh()


def clear_events() -> None:

    EVENTS.clear()

    render_events.refresh()


def handle_job_event(
    event_payload: dict
) -> None:

    append_event(event_payload)

    notify_job_subscribers(event_payload)


def register_job_event_listener() -> None:

    ui.on(
        "job_event",
        lambda e: handle_job_event(e.args)
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

async def connect_job_stream(
    job_id: str
) -> None:

    event_url = get_job_events_url(job_id)

    ui.run_javascript(
        f"""
        if (window.eventSource) {{
            window.eventSource.close();
        }}

        window.eventSource = new EventSource(
            '{event_url}'
        );

        const handleEvent = (event) => {{

            const payload = JSON.parse(
                event.data
            );

            fetch(
                '/job-event',
                {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(payload)
                }}
            );

            const terminalStatuses = [
                'COMPLETED',
                'FAILED',
                'CANCELLED'
            ];

            if (
                terminalStatuses.includes(
                    payload.job_status
                )
            ) {{
                window.eventSource.close();
            }}
        }};

        window.eventSource.addEventListener(
            'job.queued',
            handleEvent
        );

        window.eventSource.addEventListener(
            'job.running',
            handleEvent
        );

        window.eventSource.addEventListener(
            'job.completed',
            handleEvent
        );

        window.eventSource.addEventListener(
            'job.failed',
            handleEvent
        );

        window.eventSource.addEventListener(
            'job.cancelled',
            handleEvent
        );

        window.eventSource.addEventListener(
            'slots.synced',
            handleEvent
        );

        window.eventSource.addEventListener(
            'metadata.synced',
            handleEvent
        );

        window.eventSource.addEventListener(
            'download.recover',
            handleEvent
        );

        window.eventSource.addEventListener(
            'download.completes',
            handleEvent
        );

        window.eventSource.addEventListener(
            'process.recover',
            handleEvent
        );

        window.eventSource.addEventListener(
            'process.ready',
            handleEvent
        );

        window.eventSource.addEventListener(
            'process.completed',
            handleEvent
        );

        window.eventSource.addEventListener(
            'slot.active',
            handleEvent
        );

        window.eventSource.addEventListener(
            'cycle.completed',
            handleEvent
        );

        window.eventSource.onerror = (error) => {{
            console.error(
                'SSE connection error:',
                error
            );
        }};
        """
    )

def event_stream_panel() -> None:

    register_job_event_listener()

    with ui.column().classes(
        """
        w-[420px]
        shrink-0
        rounded-xl
        bg-white
        border
        border-gray-200
        p-5
        gap-5
        shadow-sm
        h-[760px]
        """
    ):

        with ui.row().classes(
            "w-full items-center justify-between"
        ):

            ui.label(
                "Event Stream"
            ).classes(
                "text-2xl font-semibold text-gray-800"
            )

            ui.button(
                "Clear",
                on_click=clear_events
            ).classes(
                """
                h-10
                px-4
                rounded-lg
                bg-blue-600
                text-white
                text-sm
                font-medium
                """
            )

        with ui.scroll_area().classes(
            "w-full flex-grow"
        ):

            with ui.column().classes(
                "w-full gap-3"
            ):

                render_events()