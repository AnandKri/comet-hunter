from nicegui import ui
from services.api import build_job_events_url

async def connect_job_stream(
    job_id: str
) -> None:

    event_url = build_job_events_url(job_id)

    ui.run_javascript(
        f"""
        if (window.eventSource) {{
            window.eventSource.close();
        }}

        window.eventSource = new EventSource(
            '{event_url}'
        );

        const handleEvent = (event) => {{

            const payload = JSON.parse(
                event.data
            );

            fetch(
                '/job-event',
                {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(payload)
                }}
            );

            const terminalStatuses = [
                'COMPLETED',
                'FAILED',
                'CANCELLED'
            ];

            if (
                terminalStatuses.includes(
                    payload.job_status
                )
            ) {{
                window.eventSource.close();
            }}
        }};

        window.eventSource.addEventListener(
            'job.queued',
            handleEvent
        );

        window.eventSource.addEventListener(
            'job.running',
            handleEvent
        );

        window.eventSource.addEventListener(
            'job.completed',
            handleEvent
        );

        window.eventSource.addEventListener(
            'job.failed',
            handleEvent
        );

        window.eventSource.addEventListener(
            'job.cancelled',
            handleEvent
        );

        window.eventSource.addEventListener(
            'slots.synced',
            handleEvent
        );

        window.eventSource.addEventListener(
            'metadata.synced',
            handleEvent
        );

        window.eventSource.addEventListener(
            'download.recover',
            handleEvent
        );

        window.eventSource.addEventListener(
            'download.completes',
            handleEvent
        );

        window.eventSource.addEventListener(
            'process.recover',
            handleEvent
        );

        window.eventSource.addEventListener(
            'process.ready',
            handleEvent
        );

        window.eventSource.addEventListener(
            'process.completed',
            handleEvent
        );

        window.eventSource.addEventListener(
            'slot.active',
            handleEvent
        );

        window.eventSource.addEventListener(
            'cycle.completed',
            handleEvent
        );

        window.eventSource.onerror = (error) => {{
            console.error(
                'SSE connection error:',
                error
            );
        }};
        """
    )