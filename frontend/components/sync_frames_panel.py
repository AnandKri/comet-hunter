from datetime import datetime, timedelta, timezone

from nicegui import ui

from events.sse import connect_job_stream
from services.api import (
    sync_frames,
    cancel_job
)
from state.event_store import (
    subscribe_to_job_events
)
from styles.theme import (
    PANEL_CARD,
    PANEL_TITLE,
    PRIMARY_BUTTON,
    STATUS_BADGE
)

from models.instruments import Instrument

from config import RETRIEVE_DATA_SINCE_DAYS

def sync_frames_panel() -> None:

    with ui.column().classes(f"{PANEL_CARD}"):

        ui.label(
            "Sync Frames"
        ).classes(
            f"{PANEL_TITLE}"
        )

        current_job_id: str | None = None

        now = datetime.now(
            timezone.utc
        )

        today = now.date()

        min_date = (
            today - timedelta(days=RETRIEVE_DATA_SINCE_DAYS)
        )

        selected_start = (
            now - timedelta(days=2)
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        selected_end = (
            now - timedelta(days=1)
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        instrument = ui.radio(
            {
                Instrument.C2.value: "C2",
                Instrument.C3.value: "C3"
            },
            value=Instrument.C3.value
        ).props(
            "inline"
        )

        with ui.row().classes(
            "w-full items-center gap-2"
        ):

            ui.label(
                "Start"
            ).classes(
                "w-[60px] text-base text-gray-700"
            )

            start_input = ui.input(
                value=selected_start.strftime(
                    "%Y-%m-%d %H:%M"
                )
            ).props(
                "dense"
            ).classes(
                "flex-grow"
            )

            with start_input.add_slot(
                "append"
            ):

                ui.icon(
                    "event"
                ).classes(
                    "cursor-pointer"
                )

            with ui.menu() as start_menu:

                with ui.column().classes(
                    "gap-2 p-2"
                ):

                    start_picker = ui.date(
                        value=selected_start.date().isoformat()
                    )

                    start_time = ui.time(
                        value=selected_start.strftime(
                            "%H:%M"
                        )
                    )

                    def apply_start_datetime():

                        nonlocal selected_start

                        selected_start = datetime.fromisoformat(
                            f"{start_picker.value}T{start_time.value}"
                        ).replace(
                            tzinfo=timezone.utc
                        )

                        start_input.set_value(
                            selected_start.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                        )

                        start_menu.close()

                    ui.button(
                        "Apply",
                        on_click=apply_start_datetime
                    )

            start_input.on(
                "click",
                lambda: start_menu.open()
            )

        with ui.row().classes(
            "w-full items-center gap-2"
        ):

            ui.label(
                "End"
            ).classes(
                "w-[60px] text-base text-gray-700"
            )

            end_input = ui.input(
                value=selected_end.strftime(
                    "%Y-%m-%d %H:%M"
                )
            ).props(
                "dense"
            ).classes(
                "flex-grow"
            )

            with end_input.add_slot(
                "append"
            ):

                ui.icon(
                    "event"
                ).classes(
                    "cursor-pointer"
                )

            with ui.menu() as end_menu:

                with ui.column().classes(
                    "gap-2 p-2"
                ):

                    end_picker = ui.date(
                        value=selected_end.date().isoformat()
                    )

                    end_time = ui.time(
                        value=selected_end.strftime(
                            "%H:%M"
                        )
                    )

                    def apply_end_datetime():

                        nonlocal selected_end

                        selected_end = datetime.fromisoformat(
                            f"{end_picker.value}T{end_time.value}"
                        ).replace(
                            tzinfo=timezone.utc
                        )

                        end_input.set_value(
                            selected_end.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                        )

                        end_menu.close()

                    ui.button(
                        "Apply",
                        on_click=apply_end_datetime
                    )

            end_input.on(
                "click",
                lambda: end_menu.open()
            )

        with ui.row().classes(
            "items-center gap-2"
        ):

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

        async def start_sync_click() -> None:

            nonlocal current_job_id

            try:

                start = selected_start.date()
                end = selected_end.date()

            except Exception:

                ui.notify(
                    "Invalid date selection",
                    type="negative"
                )

                return

            if start > end:

                ui.notify(
                    "Start date must be before end date",
                    type="warning"
                )

                return

            if (
                start < min_date
                or end < min_date
                or start > today
                or end > today
            ):

                ui.notify(
                    f"Date range must be within last {RETRIEVE_DATA_SINCE_DAYS} days",
                    type="warning"
                )

                return

            start_iso = selected_start.isoformat()
            end_iso = selected_end.isoformat()

            response = sync_frames(
                instrument.value,
                start_iso,
                end_iso
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

        def stop_sync_click() -> None:

            if not current_job_id:
                return

            success = cancel_job(
                current_job_id
            )

            if not success:

                ui.notify(
                    "Unable to cancel sync job",
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

        with ui.row().classes(
            "w-full gap-1"
        ):

            start_button = ui.button(
                "Start Sync",
                on_click=start_sync_click
            ).classes(
                f"{PRIMARY_BUTTON} flex-1"
            )

            stop_button = ui.button(
                "Stop Sync",
                on_click=stop_sync_click
            ).classes(
                f"{PRIMARY_BUTTON} flex-1"
            )

            stop_button.disable()