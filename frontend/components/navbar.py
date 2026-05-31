from nicegui import ui
from config import TITLE, SUNGRAZER_URL, DOCS_URL, GITHUB_URL
from styles.theme import NAVBAR, NAVBAR_LINK

def navbar() -> None:

    with ui.row().classes(f"{NAVBAR}"):

        ui.label(TITLE).classes("text-xl tracking-wide")

        with ui.row().classes("items-center gap-5"):

            ui.link("Sungrazer Project", SUNGRAZER_URL).classes(f"{NAVBAR_LINK}")
            ui.link("Docs", DOCS_URL).classes(f"{NAVBAR_LINK}")
            ui.link("Github", GITHUB_URL).classes(f"{NAVBAR_LINK}")