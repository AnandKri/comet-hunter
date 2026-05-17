from backend.util.enums import Instrument
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Any

class ProcessedFileResponse(BaseModel):
    processed_file_name: str
    instrument: Instrument
    processed_file_path: str
    datetime_of_observation: datetime 

class GetFramesResponse(BaseModel):
    files: list[ProcessedFileResponse]

class SyncFramesResponse(BaseModel):
    metadata_synced: int
    downloaded: int
    marked_ready: int
    processed: int

class SyncSlotsResponse(BaseModel):
    status: str
    slots_synced: int

class SchedulerStatusResponse(BaseModel):
    running: bool
    next_run_at: Optional[datetime]
    next_run_in: Optional[timedelta]

class SchedulerStartResponse(BaseModel):
    started: bool
    running: bool

class SchedulerStopResponse(BaseModel):
    stopped: bool
    running: bool

class HealthResponse(BaseModel):
    status: str
    database: bool
    scheduler_initialized: bool
    pipeline_initialized: bool

class SlotResponse(BaseModel):
    start: Optional[datetime]
    end: Optional[datetime]

class JobQueuedResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Any]
    error: Optional[str]