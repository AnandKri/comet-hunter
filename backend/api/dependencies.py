from pathlib import Path
from backend.database.infrastructure.query_executor import QueryExecutor
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.services.metadata_service import MetadataService
from backend.services.download_file_service import DownloadFileService
from backend.services.process_file_service import ProcessFileService
from backend.services.slot_service import SlotService
from backend.pipeline.pipeline import Pipeline
from backend.pipeline.scheduler import Scheduler
from backend.jobs.job_store import job_store, JobStore
from backend.jobs.background_job_service import BackgroundJobService

background_job_service = BackgroundJobService(job_store)

executor = QueryExecutor()

metadata_repo = FileMetadataRepository(executor)
processed_repo = ProcessedFileRepository(executor)
slot_repo = DownlinkSlotRepository(executor)

metadata_service = MetadataService(metadata_repo)
slot_service = SlotService(slot_repo)
download_service = DownloadFileService(
    processed_repository=processed_repo,
    metadata_service=metadata_service,
    download_directory=Path("data/raw"),
)
process_service = ProcessFileService(
    processed_repository=processed_repo,
    metadata_service=metadata_service,
    processed_directory=Path("data/processed"),
)

pipeline = Pipeline(
    slot_service=slot_service,
    metadata_service=metadata_service,
    download_service=download_service,
    process_service=process_service,
)

scheduler = Scheduler(pipeline)

def get_pipeline() -> Pipeline:
    """
    Returns shared pipeline instance for handling API requests and background jobs.
    """
    return pipeline

def get_scheduler() -> Scheduler:
    """
    Returns shared scheduler instance for triggering background jobs.
    """
    return scheduler

def get_job_store() -> JobStore:
    """
    Returns a shared job_store instance.
    """
    return job_store

def get_job_service() -> BackgroundJobService:
    """
    Returns shared background job service instance.
    Used for submitting and managing background jobs.
    """
    return background_job_service