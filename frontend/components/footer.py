from nicegui import ui

def footer() -> None:

    with ui.row().classes("w-full items-center justify-center gap-6 bg-black text-white px-8 h-[72px] text-lg shadow-sm"):

        ui.label("© 2026 Comet Hunter")
        ui.label("|").classes("text-gray-500")
        ui.label("Developed by Anand Krishna").classes("font-semibold tracking-wide")
        ui.label("|").classes("text-gray-500")
        ui.label("All rights reserved.")