from backend.jobs.job_store import job_store
from backend.util.enums import JobStatus

def run_job(job_id: str, fn, *args, **kwargs):
    """
    Executes a background job function while managing 
    its lifecycle state in the job store.
    """
    try:

        job_store.update_job(
            job_id,
            JobStatus.RUNNING
        )

        result = fn(*args, **kwargs)

        job_store.update_job(
            job_id,
            JobStatus.COMPLETED,
            result=result.__dict__ if hasattr(result, "__dict__") else result
        )

    except Exception as e:

        job_store.update_job(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )