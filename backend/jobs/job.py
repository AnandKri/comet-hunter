from dataclasses import dataclass
from typing import Optional, Any
from backend.util.enums import JobStatus

@dataclass
class Job:
    id: str
    type: str
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None