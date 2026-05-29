from nicegui import ui
from services.api import get_active_slot, get_next_active_slot

def load_active_slot( start_input: ui.input, end_input: ui.input) -> None:
    
    slot = get_active_slot()
    if not slot:
        return
    start_input.value = slot["start"]
    end_input.value = slot["end"]

def load_next_slot(start_input: ui.input, end_input: ui.input) -> None:

    slot = get_next_active_slot()
    if not slot:
        return
    start_input.value = slot["start"]
    end_input.value = slot["end"]

def active_slot_panel() -> None:

    with ui.column().classes("w-full rounded-xl bg-white border border-gray-200 p-3 gap-2 shadow-sm"):

        ui.label("Active Slot Information").classes("text-lg font-semibold text-gray-800")

        with ui.column().classes("w-full gap-2"):

            with ui.row().classes("w-full items-center gap-2"):

                ui.label("Start").classes("w-[70px] text-base text-gray-700")
                start_input = ui.input().props("readonly outlined").classes("flex-grow")

            with ui.row().classes("w-full items-center gap-2"):

                ui.label("End").classes("w-[70px] text-base text-gray-700")
                end_input = ui.input().props("readonly outlined").classes("flex-grow")

        with ui.row().classes("w-full gap-1"):

            ui.button("Get Active Slot", on_click = lambda: load_active_slot(start_input,end_input)).classes(
                "flex-1 h-5 rounded-lg bg-blue-600 text-white text-sm font-medium whitespace-nowrap"
                )

            ui.button("Get Next Slot", on_click = lambda: load_next_slot(start_input,end_input)).classes(
                "flex-1 h-5 rounded-lg bg-blue-600 text-white text-sm font-medium whitespace-nowrap"
            )