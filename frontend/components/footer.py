from nicegui import ui
from config import TITLE, DEVELOPER_NAME, VERSION
from styles.theme import FOOTER

def footer() -> None:

    with ui.row().classes(f"{FOOTER}"):

        ui.label(f"{TITLE} v{VERSION}")
        ui.label("|").classes("text-gray-500")
        ui.label(f"Developed by {DEVELOPER_NAME}").classes("tracking-wide")