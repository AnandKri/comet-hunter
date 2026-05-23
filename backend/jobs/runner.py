from backend.jobs.job_store import job_store
from backend.util.enums import JobStatus
from datetime import datetime, UTC
from backend.jobs.exceptions import CancelledError

def run_job(job_id: str, fn, *args, **kwargs):
    """
    Executes a background job function while managing 
    its lifecycle state in the job store.
    """
    try:

        job = job_store.get_job(job_id)

        job_store.update_job(
            job_id,
            JobStatus.RUNNING,
            started_at=datetime.now(UTC),
            progress="Started"
        )

        result = fn(
            *args,
            cancel_event = job.cancel_event,
            **kwargs
        )

        job_store.update_job(
            job_id,
            JobStatus.COMPLETED,
            stopped_at=datetime.now(UTC),
            progress="Completed",
            result=result.__dict__ if hasattr(result, "__dict__") else result
        )
    
    except CancelledError as c:

        job_store.update_job(
            job_id,
            JobStatus.CANCELLED,
            stopped_at=datetime.now(UTC),
            progress="Cancelled",
            error=str(c)
        )

    except Exception as e:

        job_store.update_job(
            job_id,
            JobStatus.FAILED,
            stopped_at=datetime.now(UTC),
            progress="Failed",
            error=str(e)
        )