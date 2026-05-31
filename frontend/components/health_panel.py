from nicegui import ui
from services.api import health_check
from styles.theme import STATUS_BADGE, PANEL_CARD, PANEL_TITLE, ROW_BETWEEN, PRIMARY_BUTTON

def check_backend(status_label: ui.label) -> None:

    healthy = health_check()

    if healthy:
        status_label.set_text("HEALTHY")
        status_label.classes(replace=f"{STATUS_BADGE} bg-green-100 text-green-700")
    else:
        status_label.set_text("DOWN")
        status_label.classes(replace=f"{STATUS_BADGE} bg-red-100 text-red-700")

def health_panel() -> None:

    with ui.column().classes(f"{PANEL_CARD}"):

        ui.label("System Health").classes(f"{PANEL_TITLE}")

        with ui.row().classes(f"{ROW_BETWEEN}"):

            with ui.row().classes("items-center gap-2"):

                ui.label("Status").classes("text-sm text-gray-700")
                status_label = ui.label("UNKNOWN").classes(f"{STATUS_BADGE} bg-gray-100 text-gray-700")

            ui.button("Check Health", on_click=lambda: check_backend(status_label)).classes(f"{PRIMARY_BUTTON}")