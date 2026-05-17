from datetime import UTC, datetime

from nicegui import ui


def utc_clock() -> None:

    with ui.card().classes("w-full bg-white border border-gray-200 rounded-xl shadow-sm p-5"):

        datetime_label = ui.label().classes("text-2xl text-black")

    def update_time() -> None:
        now = datetime.now(UTC)
        datetime_label.set_text(now.strftime("%a %b %d %Y %H:%M:%S UTC"))

    update_time()

    ui.timer(interval=1.0,callback=update_time)