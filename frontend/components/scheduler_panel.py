from nicegui import ui

from events.sse import connect_job_stream
from services.api import (
    start_scheduler,
    cancel_job
)
from state.event_store import (
    subscribe_to_job_events
)
from styles.theme import (
    PANEL_CARD,
    PANEL_TITLE,
    PRIMARY_BUTTON,
    STATUS_BADGE,
    ROW_BETWEEN
)
from models.instruments import Instrument

def scheduler_panel() -> None:

    with ui.column().classes(f"{PANEL_CARD}"):

        ui.label(
            "Scheduler"
        ).classes(
            f"{PANEL_TITLE}"
        )

        instrument_select = ui.select(
            options=[Instrument.C2.value, Instrument.C3.value],
            multiple=True,
            value=[Instrument.C3.value]
        ).props(
            "outlined dense"
        ).classes(
            "w-full"
        )

        current_job_id: str | None = None

        async def start_scheduler_click() -> None:

            nonlocal current_job_id

            instruments = instrument_select.value or []

            if not instruments:
                ui.notify(
                    "Select at least one instrument",
                    type="warning"
                )
                return

            response = start_scheduler(
                instruments
            )

            if not response:

                status_label.set_text(
                    "FAILED"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-red-100 text-red-700 min-w-[110px] text-center"
                )

                return

            current_job_id = response.job_id

            start_button.disable()
            stop_button.enable()

            status_label.set_text(
                "RUNNING"
            )

            status_label.classes(
                replace=f"{STATUS_BADGE} bg-yellow-100 text-yellow-700 min-w-[110px] text-center"
            )

            await connect_job_stream(
                current_job_id
            )

        def stop_scheduler_click() -> None:

            if not current_job_id:
                return

            success = cancel_job(
                current_job_id
            )

            if not success:
                ui.notify(
                    "Unable to cancel scheduler",
                    type="negative"
                )

        def handle_stream_event(
            event_payload: dict
        ) -> None:

            nonlocal current_job_id

            if (
                event_payload.get("job_id")
                != current_job_id
            ):
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

            elif status == "CANCELLING":

                status_label.set_text(
                    "CANCELLING"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-orange-100 text-orange-700 min-w-[110px] text-center"
                )

            elif status == "CANCELLED":

                status_label.set_text(
                    "CANCELLED"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-gray-200 text-gray-700 min-w-[110px] text-center"
                )

                start_button.enable()
                stop_button.disable()

                current_job_id = None

            elif status == "COMPLETED":

                status_label.set_text(
                    "COMPLETED"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-green-100 text-green-700 min-w-[110px] text-center"
                )

                start_button.enable()
                stop_button.disable()

                current_job_id = None

            elif status == "FAILED":

                status_label.set_text(
                    "FAILED"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-red-100 text-red-700 min-w-[110px] text-center"
                )

                start_button.enable()
                stop_button.disable()

                current_job_id = None

        subscribe_to_job_events(
            handle_stream_event
        )

        with ui.row().classes("items-center gap-2"):

            ui.label(
                "Status"
            ).classes(
                "text-base text-gray-700"
            )

            status_label = ui.label(
                "IDLE"
            ).classes(
                f"{STATUS_BADGE} bg-gray-100 text-gray-700 min-w-[110px] text-center"
            )

        with ui.row().classes(
            "w-full gap-1"
        ):

            start_button = ui.button(
                "Start",
                on_click=start_scheduler_click
            ).classes(
                f"{PRIMARY_BUTTON} flex-1"
            )

            stop_button = ui.button(
                "Stop",
                on_click=stop_scheduler_click
            ).classes(
                f"{PRIMARY_BUTTON} flex-1"
            )

            stop_button.disable()