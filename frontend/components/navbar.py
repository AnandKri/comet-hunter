from nicegui import ui
from config import TITLE, SUNGRAZER_URL, DOCS_URL, GITHUB_URL

def navbar() -> None:

    with ui.row().classes("w-full items-center justify-between px-8 h-[74px] bg-black text-white shadow-sm"):

        ui.label(TITLE).classes("text-4xl font-bold tracking-wide")

        with ui.row().classes("items-center gap-10"):

            ui.link("Sungrazer Project", SUNGRAZER_URL).classes("text-lg font-medium text-white no-underline hover:text-gray-300")
            ui.link("Docs", DOCS_URL).classes("text-lg font-medium text-white no-underline hover:text-gray-300")
            ui.link("Github", GITHUB_URL).classes("text-lg font-medium text-white no-underline hover:text-gray-300")