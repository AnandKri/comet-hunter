from typing import Optional, Any
from backend.jobs.job import Job
from backend.util.enums import JobStatus
import uuid


class JobStore:
    """
    In-memory store for tracking background job execution state.

    Responsibilities:
    - Create new jobs
    - Retrieve existing jobs
    - Update job lifecycle status
    - Store job results and errors

    Notes:
    - Data is stored only in memory.
    - Job state is lost if application restarts.
    - Intended for lightweight single-instance usage.
    """

    def __init__(self) -> None:
        """
        Initialize empty in-memory job storage.
        """

        self._jobs: dict[str, Job] = {}

    def create_job(self, type: str) -> Job:
        """
        Create and register a new background job.

        Newly created jobs begin in QUEUED state.

        :param type:
            string to categorize or identify the job type.
        :return:
            Created Job domain entity.
        """

        job = Job(
            id=str(uuid.uuid4()),
            type=type,
            status=JobStatus.QUEUED
        )

        self._jobs[job.id] = job

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Retrieve job by identifier.

        :param job_id:
            Unique job identifier.

        :return:
            Job entity if found, otherwise None.
        """

        return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> Optional[Job]:
        """
        Update existing job state and metadata.

        Allows updating:
        - lifecycle status
        - result payload
        - failure error message

        :param job_id:
            Unique identifier of the job.

        :param status:
            Updated lifecycle status.

        :param result:
            Optional result payload produced by the job.

        :param error:
            Optional error message if job failed.

        :return:
            Updated Job entity if found, otherwise None.
        """

        job = self.get_job(job_id)

        if job is None:
            return None

        job.status = status
        job.result = result
        job.error = error

        return job

job_store = JobStore()