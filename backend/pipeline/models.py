from backend.database.domain.processed_file import ProcessedFile
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Optional

@dataclass
class RunLivePipelineResult:
    metadata_synced: int
    downloaded: int
    next_run: Optional[timedelta]

@dataclass
class GetProcessedFramesResult:
    processed_files: list[ProcessedFile]

@dataclass
class SyncProcessedFramesResult:
    metadata_synced: int
    downloaded: int
    marked_ready: int
    processed: int

@dataclass
class SyncSlotsResult:
    slots_synced: int

@dataclass
class SchedulerStatusResult:
    running: bool
    next_run_at: Optional[datetime]
    next_run_in: Optional[timedelta]

@dataclass
class SchedulerStartResult:
    response: int

@dataclass
class SchedulerShutdownResult:
    response: int