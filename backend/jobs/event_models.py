from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any
from backend.util.enums import JobStatus, JobType

@dataclass(frozen=True)
class JobEvent:
    """
    Standardized realtime event payload for background jobs.

    This model acts as the canonical event envelope for:
    - SSE streaming
    - realtime monitoring
    - job observability
    - frontend event handling

    Attributes:
        job_id:
            Unique identifier of the related job.
        job_type:
            Type/category of background job.
        job_status:
            Current lifecycle status of the job.
        event:
            Semantic event name.

            Examples:
            - job.started
            - job.completed
            - metadata.synced
            - processing.progress
        timestamp:
            UTC timestamp when event occurred.
        data:
            Event-specific payload.
    """
    job_id: str
    job_type: JobType
    job_status: JobStatus
    event: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: dict[str, Any] = field(default_factory=dict)