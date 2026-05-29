from nicegui import ui
from services.api import sync_slots
from components.event_stream_panel import (
    connect_job_stream,
    subscribe_to_job_events
)

def sync_slots_panel() -> None:

    with ui.column().classes("w-full rounded-xl bg-white border border-gray-200 p-3 gap-2 shadow-sm"):

        ui.label("Sync Slots").classes("text-lg font-semibold text-gray-800")

        status_label = ui.label("IDLE").classes("text-sm px-2 py-1 rounded-full bg-gray-100 text-gray-700 w-fit")

        result_label = ui.label("").classes("text-lg text-gray-700")

        current_job_id: str | None = None

        def handle_stream_event(
            event_payload: dict
        ) -> None:

            nonlocal current_job_id

            if (event_payload.get("job_id") != current_job_id):
                return

            status = event_payload.get("job_status","")
            event_name = event_payload.get("event","")

            if status == "RUNNING":
                status_label.set_text("RUNNING")
                status_label.classes(replace= "text-sm px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 w-fit")

            elif status == "COMPLETED":

                status_label.set_text("COMPLETED")
                status_label.classes(replace= "text-sm px-2 py-1 rounded-full bg-green-100 text-green-700 w-fit")
                result_label.set_text("Slot synchronization completed")
                sync_button.enable()
                current_job_id = None

            elif status == "FAILED":

                status_label.set_text("FAILED")
                status_label.classes( replace= "text-sm px-2 py-1 rounded-full bg-red-100 text-red-700 w-fit")
                result_label.set_text("Slot synchronization failed")
                sync_button.enable()
                current_job_id = None

            elif event_name == "slots.synced":
                data = event_payload.get("data",{})
                synced = data.get("slots_synced","?")
                result_label.set_text(f"{synced} slots synced")

        subscribe_to_job_events(handle_stream_event)

        async def start_sync() -> None:

            nonlocal current_job_id

            response = sync_slots()

            if not response:

                status_label.set_text("FAILED")

                status_label.classes(
                    replace="text-sm px-2 py-1 rounded-full bg-red-100 text-red-700 w-fit")

                result_label.set_text("Unable to start sync job")

                return

            current_job_id = response["job_id"]

            sync_button.disable()

            status_label.set_text("RUNNING")

            status_label.classes(replace= "text-sm px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 w-fit")

            result_label.set_text("Syncing slots...")

            await connect_job_stream(current_job_id)

        sync_button = ui.button("Sync Slots",on_click=start_sync).props("type=button").classes("w-full h-5 rounded-lg bg-blue-600 text-white text-sm font-medium")