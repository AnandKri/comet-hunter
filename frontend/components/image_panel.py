from nicegui import ui

from config import SERVER_BASE_URL, TEMP_IMAGE_URL

from state.frame_store import (
    current_frame,
    current_position,
    total_frames,
    next_frame,
    previous_frame,
    subscribe_to_frame_updates
)
from styles.theme import (
    PANEL_CARD,
    PANEL_TITLE,
    PRIMARY_BUTTON
)


def image_panel() -> None:

    image = None
    filename_label = None
    instrument_label = None
    observation_label = None
    counter_label = None

    def refresh_panel() -> None:

        frame = current_frame()

        if frame is None:

            image.set_source(TEMP_IMAGE_URL)

            filename_label.set_text(
                "Filename: -"
            )

            instrument_label.set_text(
                "Instrument: -"
            )

            observation_label.set_text(
                "Observation: -"
            )

            counter_label.set_text(
                "0 / 0"
            )

            return

        image.set_source(
            f"{SERVER_BASE_URL}{frame.processed_file_url}"
        )

        filename_label.set_text(
            f"Filename: {frame.processed_file_name}"
        )

        instrument_label.set_text(
            f"Instrument: {frame.instrument}"
        )

        observation_label.set_text(
            f"Observation: {frame.datetime_of_observation}"
        )

        counter_label.set_text(
            f"{current_position()} / {total_frames()}"
        )

    with ui.column().classes(
        f"{PANEL_CARD} w-full h-full items-center"
    ):

        ui.label(
            "Processed Frames"
        ).classes(
            f"{PANEL_TITLE}"
        )

        image = ui.image(
            TEMP_IMAGE_URL
        ).classes(
            """
            w-[800px]
            h-[800px]
            border
            border-gray-200
            rounded-lg
            object-contain
            """
        )

        filename_label = ui.label(
            "Filename: -"
        )

        instrument_label = ui.label(
            "Instrument: -"
        )

        observation_label = ui.label(
            "Observation: -"
        )

        counter_label = ui.label(
            "0 / 0"
        ).classes(
            "font-medium"
        )

        with ui.row().classes(
            "w-full gap-1"
        ):

            ui.button(
                "Previous",
                on_click=previous_frame
            ).classes(
                f"{PRIMARY_BUTTON} flex-1"
            )

            ui.button(
                "Next",
                on_click=next_frame
            ).classes(
                f"{PRIMARY_BUTTON} flex-1"
            )

    subscribe_to_frame_updates(
        refresh_panel
    )

    refresh_panel()