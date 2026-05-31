from nicegui import ui
from services.api import sync_slots
from state.event_store import subscribe_to_job_events
from events.sse import connect_job_stream
from styles.theme import (
    PANEL_CARD,
    PANEL_TITLE,
    PRIMARY_BUTTON,
    STATUS_BADGE,
    ROW_BETWEEN
)


def sync_slots_panel() -> None:

    with ui.column().classes(f"{PANEL_CARD}"):

        ui.label("Sync Slots").classes(f"{PANEL_TITLE}")

        current_job_id: str | None = None

        async def start_sync() -> None:

            nonlocal current_job_id

            response = sync_slots()

            if not response:

                status_label.set_text("FAILED")
                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-red-100 text-red-700 min-w-[110px] text-center"
                )

                return

            current_job_id = response.job_id

            sync_button.disable()

            status_label.set_text("RUNNING")
            status_label.classes(
                replace=f"{STATUS_BADGE} bg-yellow-100 text-yellow-700 min-w-[110px] text-center"
            )

            await connect_job_stream(current_job_id)

        with ui.row().classes(f"{ROW_BETWEEN}"):

            with ui.row().classes("items-center gap-2"):

                ui.label("Status").classes(
                    "text-sm text-gray-700"
                )

                status_label = ui.label(
                    "IDLE"
                ).classes(
                    f"{STATUS_BADGE} bg-gray-100 text-gray-700 min-w-[110px] text-center"
                )

            sync_button = ui.button(
                "Sync Slots",
                on_click=start_sync
            ).props(
                "type=button"
            ).classes(
                f"{PRIMARY_BUTTON}"
            )

        def handle_stream_event(
            event_payload: dict
        ) -> None:

            nonlocal current_job_id

            if event_payload.get("job_id") != current_job_id:
                return

            status = event_payload.get(
                "job_status",
                ""
            )

            if status == "RUNNING":

                status_label.set_text(
                    "RUNNING"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-yellow-100 text-yellow-700 min-w-[110px] text-center"
                )

            elif status == "COMPLETED":

                status_label.set_text(
                    "COMPLETED"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-green-100 text-green-700 min-w-[110px] text-center"
                )

                sync_button.enable()
                current_job_id = None

            elif status == "FAILED":

                status_label.set_text(
                    "FAILED"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-red-100 text-red-700 min-w-[110px] text-center"
                )

                sync_button.enable()
                current_job_id = None

        subscribe_to_job_events(
            handle_stream_event
        )