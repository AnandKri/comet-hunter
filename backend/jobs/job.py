from dataclasses import dataclass
from typing import Optional, Any
from backend.util.enums import JobStatus, JobType
from datetime import datetime

@dataclass
class Job:
    id: str
    type: JobType
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    progress: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[str] = None