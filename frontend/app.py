from nicegui import ui, app
from config import TITLE, PORT
from components.footer import footer
from components.health_panel import health_panel
from components.image_panel import image_panel
from components.navbar import navbar
from components.active_slot_panel import active_slot_panel
from components.utc_clock import utc_clock
from components.sync_slots_panel import sync_slots_panel
from components.event_stream_panel import event_stream_panel, handle_job_event
from fastapi import Request

def build_layout() -> None:

    ui.page_title(TITLE)

    ui.query("body").style(
        """
        background-color: #f3f4f6;
        font-family: Inter, sans-serif;
        margin: 0;
        padding: 0;
        """
    )

    with ui.column().classes(
        "w-full min-h-screen gap-1"
    ):

        navbar()

        with ui.row().classes(
            "w-full items-start gap-1 flex-grow no-wrap"
        ):

            event_stream_panel()

            with ui.column().classes(
                "w-[350px] shrink-0 gap-1"
            ):

                health_panel()
                utc_clock()
                active_slot_panel()
                sync_slots_panel()

            with ui.column().classes(
                "flex-grow"
            ):

                image_panel()

        footer()


@app.post("/job-event")
async def receive_job_event(
    request: Request
) -> dict:

    payload = await request.json()

    handle_job_event(payload)

    return {"success": True}

def main() -> None:

    build_layout()

    ui.run(
        host="0.0.0.0",
        port=PORT,
        reload=True,
        title=TITLE
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()