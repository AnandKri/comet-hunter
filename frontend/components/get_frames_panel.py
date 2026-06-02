from datetime import datetime, timedelta, timezone

from nicegui import ui

from services.api import get_frames
from state.frame_store import set_frames
from styles.theme import (
    PANEL_CARD,
    PANEL_TITLE,
    PRIMARY_BUTTON,
    STATUS_BADGE
)
from models.instruments import Instrument

from config import RETRIEVE_DATA_SINCE_DAYS

def get_frames_panel() -> None:

    with ui.column().classes(f"{PANEL_CARD}"):

        ui.label(
            "Get Frames"
        ).classes(
            f"{PANEL_TITLE}"
        )

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

        def load_frames() -> None:

            nonlocal selected_start
            nonlocal selected_end

            if selected_start >= selected_end:

                ui.notify(
                    "Start datetime must be earlier than end datetime",
                    type="warning"
                )

                return
            
            start = selected_start.date()
            end = selected_end.date()

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
            
            status_label.set_text(
                "LOADING"
            )

            status_label.classes(
                replace=f"{STATUS_BADGE} bg-yellow-100 text-yellow-700 min-w-[110px] text-center"
            )

            get_frames_button.disable()

            files = get_frames(
                instrument.value,
                selected_start.isoformat(),
                selected_end.isoformat()
            )

            if files is None:

                status_label.set_text(
                    "FAILED"
                )

                status_label.classes(
                    replace=f"{STATUS_BADGE} bg-red-100 text-red-700 min-w-[110px] text-center"
                )

                get_frames_button.enable()

                return

            set_frames(
                files
            )

            status_label.set_text(
                "COMPLETED"
            )

            status_label.classes(
                replace=f"{STATUS_BADGE} bg-green-100 text-green-700 min-w-[110px] text-center"
            )

            ui.notify(
                f"{len(files)} frames loaded"
            )

            get_frames_button.enable()

        get_frames_button = ui.button(
            "Get Frames",
            on_click=load_frames
        ).classes(
            f"{PRIMARY_BUTTON} w-full"
        )