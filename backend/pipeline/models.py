from backend.database.domain.processed_file import ProcessedFile
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

@dataclass
class RunLivePipelineResult:
    metadata_synced: int
    downloaded: int
    next_run: Optional[timedelta]

@dataclass
class GetProcessedFramesResult:
    metadata_synced: int
    downloaded: int
    marked_ready: int
    processed: int
    processed_files: list[ProcessedFile]