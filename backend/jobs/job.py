from dataclasses import dataclass, field
from typing import Optional, Any
from threading import Event
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
    cancel_event: Event = field(default_factory=Event)
    progress: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[str] = None