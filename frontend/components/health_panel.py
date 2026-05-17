from nicegui import ui
from services.api import health_check

def check_backend(status_label: ui.label) -> None:

    healthy = health_check()

    if healthy:
        status_label.set_text("HEALTHY")
        status_label.classes(replace="text-sm font-semibold px-3 py-1 rounded-full bg-green-100 text-green-700")
    else:
        status_label.set_text("DOWN")
        status_label.classes(replace="text-sm font-semibold px-3 py-1 rounded-full bg-red-100 text-red-700")

def health_panel() -> None:

    with ui.column().classes("w-full rounded-xl bg-white border border-gray-200 p-5 shadow-sm gap-5"):

        ui.label("System Health").classes("text-2xl font-semibold text-gray-800")

        with ui.row().classes("w-full items-center justify-between"):

            with ui.row().classes("items-center gap-3"):

                ui.label("Status").classes("text-lg text-gray-700")
                status_label = ui.label("UNKNOWN").classes("text-sm font-semibold px-3 py-1 rounded-full bg-gray-100 text-gray-700")

            ui.button("Check Health", on_click=lambda: check_backend(status_label)).classes("h-11 px-6 rounded-lg bg-blue-600 text-white text-sm font-medium")