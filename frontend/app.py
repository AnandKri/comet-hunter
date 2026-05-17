from nicegui import ui
from config import TITLE, PORT
from components.footer import footer
from components.health_panel import health_panel
from components.image_panel import image_panel
from components.navbar import navbar
from components.active_slot_panel import active_slot_panel
from components.utc_clock import utc_clock
from components.sync_slots_panel import sync_slots_panel

def build_layout() -> None:

    ui.page_title(TITLE)

    ui.query("body").style("background-color: #f3f4f6; font-family: Inter, sans-serif; margin: 0; padding: 0;")

    with ui.column().classes("w-full max-w-[1600px] min-h-screen mx-auto gap-4"):

        navbar()

        with ui.row().classes("w-full items-start gap-6 flex-grow no-wrap"):
            with ui.column().classes("w-[430px] shrink-0 gap-5"):

                health_panel()
                utc_clock()
                active_slot_panel()
                sync_slots_panel()
            
            with ui.column().classes("flex-grow"):
                
                image_panel()

        footer()

def main() -> None:

    build_layout()

    ui.run(
        host="0.0.0.0",
        port=PORT,
        reload=False,
        title=TITLE
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()