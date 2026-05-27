from backend.jobs.job_store import job_store
from backend.util.enums import JobStatus
from datetime import datetime, UTC
from backend.jobs.exceptions import CancelledError
from backend.jobs.event_bus import event_bus
from backend.jobs.event_models import JobEvent

def run_job(job_id: str, fn, *args, **kwargs):
    """
    Executes a background job function while managing 
    its lifecycle state in the job store.
    """
    try:

        job = job_store.get_job(job_id)

        job_store.update_job(
            job.id,
            JobStatus.RUNNING,
            started_at=datetime.now(UTC),
            progress="Started"
        )

        event_bus.publish(
            job_id=job.id,
            event=JobEvent(
                job_id=job.id,
                job_type=job.type,
                job_status=JobStatus.RUNNING,
                event="job.running",
                data={}
            )
        )

        result = fn(
            *args,
            cancel_event=job.cancel_event,
            job_id=job.id,
            job_type=job.type,
            **kwargs
        )

        job_store.update_job(
            job_id,
            JobStatus.COMPLETED,
            stopped_at=datetime.now(UTC),
            progress="Completed",
            result=result.__dict__ if hasattr(result, "__dict__") else result
        )

        event_bus.publish(
            job_id=job.id,
            event=JobEvent(
                job_id=job.id,
                job_type=job.type,
                job_status=JobStatus.COMPLETED,
                event="job.completed",
                data={}
            )
        )
    
    except CancelledError as c:

        job_store.update_job(
            job_id,
            JobStatus.CANCELLED,
            stopped_at=datetime.now(UTC),
            progress="Cancelled",
            error=str(c)
        )

        event_bus.publish(
            job_id=job.id,
            event=JobEvent(
                job_id=job.id,
                job_type=job.type,
                job_status=JobStatus.CANCELLED,
                event="job.cancelled",
                data={}
            )
        )

    except Exception as e:

        job_store.update_job(
            job_id,
            JobStatus.FAILED,
            stopped_at=datetime.now(UTC),
            progress="Failed",
            error=str(e)
        )

        event_bus.publish(
            job_id=job.id,
            event=JobEvent(
                job_id=job.id,
                job_type=job.type,
                job_status=JobStatus.FAILED,
                event="job.failed",
                data={}
            )
        )