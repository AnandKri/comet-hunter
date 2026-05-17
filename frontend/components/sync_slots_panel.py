from nicegui import ui
from services.api import sync_slots, get_job_status

def sync_slots_panel() -> None:

    with ui.column().classes("w-full rounded-xl bg-white border border-gray-200 p-5 gap-5 shadow-sm"):

        ui.label("Sync Slots").classes("text-2xl font-semibold text-gray-800")
        status_label = ui.label("IDLE").classes("text-sm font-semibold px-3 py-1 rounded-full bg-gray-100 text-gray-700 w-fit ")
        result_label = ui.label("").classes("text-lg text-gray-700")

        current_job_id: str | None = None

        def schedule_poll() -> None:
            ui.timer(interval=2.0,callback=poll_job,once=True)

        def poll_job() -> None:

            nonlocal current_job_id
            if not current_job_id:
                return
            job = get_job_status(current_job_id)
            if not job:
                schedule_poll()
                return
            
            status = job["status"]
            if status == "COMPLETED":
                synced = job["result"]["slots_synced"]
                status_label.set_text("COMPLETED")
                status_label.classes( replace="text-sm font-semibold px-3 py-1 rounded-full bg-green-100 text-green-700 w-fit")
                result_label.set_text(f"{synced} slots synced")
                sync_button.enable()
                current_job_id = None
            elif status == "FAILED":
                status_label.set_text("FAILED")
                status_label.classes( replace="text-sm font-semibold px-3 py-1 rounded-full bg-red-100 text-red-700 w-fit")
                result_label.set_text(job.get("error") or "Sync failed")
                sync_button.enable()
                current_job_id = None
            else:
                schedule_poll()

        def start_sync() -> None:

            nonlocal current_job_id
            response = sync_slots()
            if not response:
                status_label.set_text("FAILED")
                status_label.classes( replace="text-sm font-semibold px-3 py-1 rounded-full bg-red-100 text-red-700 w-fit")
                result_label.set_text("Unable to start sync job")
                return

            current_job_id = response["job_id"]
            sync_button.disable()
            status_label.set_text("RUNNING")
            status_label.classes( replace="text-sm font-semibold px-3 py-1 rounded-full bg-yellow-100 text-yellow-700 w-fit")
            result_label.set_text("Syncing slots...")
            schedule_poll()

        sync_button = ui.button( "Sync Slots", on_click=start_sync).props("type=button").classes("w-full h-12 rounded-lg bg-blue-600 text-white text-lg font-medium")