from dataclasses import dataclass
from backend.jobs.job import Job

@dataclass
class JobSubmissionResult:
    job: Job
    existing: bool