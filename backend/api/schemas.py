from backend.util.enums import Instrument
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

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
    slots_synced: int

class SchedulerStatusResponse(BaseModel):
    running: bool
    next_run_at: Optional[datetime]
    next_run_in: Optional[timedelta]

class SchedulerStartResponse(BaseModel):
    response: int

class SchedulerShutdownResponse(BaseModel):
    response: int

class HealthResponse(BaseModel):
    database: bool
    scheduler_running: bool
    pipeline_initialized: bool