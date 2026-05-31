from dataclasses import dataclass

@dataclass
class JobQueued:
    job_id: str
    existing: bool
    status: str

@dataclass
class JobEvent:
    event: str
    job_id: str
    job_status: str
    job_type: str
    timestamp: str
    data: dict