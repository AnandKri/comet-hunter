from nicegui import ui
from config import TITLE, DEVELOPER_NAME
from datetime import datetime

def footer() -> None:

    with ui.row().classes("w-full items-center justify-center gap-2 bg-black text-white h-[50px] text-base shadow-sm"):

        ui.label(f"© {datetime.now().year} {TITLE}")
        ui.label("|").classes("text-gray-500")
        ui.label(f"Developed by {DEVELOPER_NAME}").classes("tracking-wide")
        ui.label("|").classes("text-gray-500")
        ui.label("All rights reserved.")