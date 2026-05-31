from nicegui import ui
from services.api import get_active_slot, get_next_active_slot
from styles.theme import PANEL_CARD, PANEL_TITLE, PRIMARY_BUTTON, ROW_BETWEEN

def load_active_slot( start_input: ui.input, end_input: ui.input) -> None:
    
    slot = get_active_slot()
    if not slot:
        return
    start_input.value = slot.start
    end_input.value = slot.end

def load_next_slot(start_input: ui.input, end_input: ui.input) -> None:

    slot = get_next_active_slot()
    if not slot:
        return
    start_input.value = slot.start
    end_input.value = slot.end

def active_slot_panel() -> None:

    with ui.column().classes(f"{PANEL_CARD}"):

        ui.label("Active Slot Information").classes(f"{PANEL_TITLE}")

        with ui.column().classes("w-full gap-1"):

            with ui.row().classes("w-full items-center"):

                ui.label("Start").classes("w-[30px] text-sm text-gray-700")
                start_input = ui.input().props("readonly outlined").classes("flex-grow")

            with ui.row().classes("w-full items-center"):

                ui.label("End").classes("w-[30px] text-sm text-gray-700")
                end_input = ui.input().props("readonly outlined").classes("flex-grow")

        with ui.row().classes("w-full gap-1"):

            ui.button("Get Active Slot", on_click = lambda: load_active_slot(start_input,end_input)).classes(
                f"flex-1 {PRIMARY_BUTTON} whitespace-nowrap"
                )

            ui.button("Get Next Slot", on_click = lambda: load_next_slot(start_input,end_input)).classes(
                f"flex-1 {PRIMARY_BUTTON} whitespace-nowrap"
            )