from nicegui import ui

def image_panel() -> None:

    with ui.column().classes("w-full items-center justify-center bg-white border border-gray-200 shadow-sm p-6"):

        ui.image("https://placehold.co/1000x1000").classes("w-full max-w-[1000px] aspect-square border border-gray-200")