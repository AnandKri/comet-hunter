from datetime import UTC, datetime
from styles.theme import PANEL_CARD
from nicegui import ui


def utc_clock() -> None:

    with ui.card().classes(f"{PANEL_CARD}"):

        datetime_label = ui.label().classes("text-sm text-black")

    def update_time() -> None:
        now = datetime.now(UTC)
        datetime_label.set_text(now.strftime("%a %b %d %Y %H:%M:%S UTC"))

    update_time()

    ui.timer(interval=1.0,callback=update_time)