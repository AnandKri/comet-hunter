from threading import Thread
from backend.jobs.runner import run_job
from backend.jobs.job import Job
from backend.jobs.job_store import JobStore
from backend.util.enums import JobType, JobStatus, JobEventType
from backend.jobs.job_submission import JobSubmissionResult
from backend.jobs.event_bus import event_bus
from backend.jobs.event_models import JobEvent

class BackgroundJobService:
    """
    Thin service layer for managing background jobs.

    Provides API for creating and retrieving background jobs,
    as well as executing them in separate threads while managing
    their lifecycle state.
    """
    def __init__(self, job_store: JobStore) -> None:
        self._job_store = job_store
    
    def submit(self, job_type: JobType, fn, *args, **kwargs) -> JobSubmissionResult:
        """
        Create and execute a new background job.

        :param job_type:
            Type of the background job.

        :param fn:
            Function to execute as the background job.

        :param args:
            Positional arguments to pass to the function.

        :param kwargs:
            Keyword arguments to pass to the function.

        :return:
            Created Job entity with assigned identifier and initial state.
        """

        existing_job = self._job_store.get_active_job(job_type)

        if existing_job:
            return JobSubmissionResult(
                job=existing_job,
                existing=True
            )

        job = self._job_store.create_job(job_type)

        event_bus.publish(
            job_id=job.id,
            event=JobEvent(
                job_id=job.id,
                job_type=job.type,
                job_status=JobStatus.QUEUED,
                event=JobEventType.JOB_QUEUED,
                data={}
            )
        )

        thread = Thread(target=run_job, args=(job.id, fn, *args), kwargs=kwargs, daemon=True)
        thread.start()

        return JobSubmissionResult(
            job=job,
            existing=False
        )
    
    def get_job(self, job_id: str) -> Job:
        """
        Retrieve background job details by identifier.

        :param job_id:
            Unique identifier of the background job.

        :return:
            Job entity if found, otherwise None.
        """

        return self._job_store.get_job(job_id)