from nicegui import ui
from config import TEMP_IMAGE_PANEL_SIZE, TEMP_IMAGE_URL

def image_panel() -> None:

    with ui.column().classes("w-full items-center justify-center bg-white border border-gray-200 shadow-sm p-6"):

        ui.image(TEMP_IMAGE_URL).classes(f"w-full max-w-[{TEMP_IMAGE_PANEL_SIZE}px] aspect-square border border-gray-200")