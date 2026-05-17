from nicegui import ui


def navbar() -> None:

    with ui.row().classes("w-full items-center justify-between px-8 h-[74px] bg-black text-white shadow-sm"):

        ui.label("Comet Hunter").classes("text-4xl font-bold tracking-wide")

        with ui.row().classes("items-center gap-10"):

            ui.link("Sungrazer Project","https://sungrazer.nrl.navy.mil/").classes("text-lg font-medium text-white no-underline hover:text-gray-300")
            ui.link("Docs","https://anandkri.github.io/comet-hunter/").classes("text-lg font-medium text-white no-underline hover:text-gray-300")
            ui.link("Github","https://github.com/anandkri/comet-hunter").classes("text-lg font-medium text-white no-underline hover:text-gray-300")