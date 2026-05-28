from backend.services.slot_service import SlotService
from backend.services.metadata_service import MetadataService
from backend.services.download_file_service import DownloadFileService
from backend.services.process_file_service import ProcessFileService
from backend.util.enums import Instrument, FileStatus, JobStatus, JobType, JobEventType
from backend.pipeline.models import RunIngestionCycleResult, GetProcessedFramesResult, SyncProcessedFramesResult, SyncSlotsResult, SlotResult
from backend.util.funcs import parse_utc_datetime
from backend.jobs.exceptions import CancelledError
from backend.jobs.event_models import JobEvent
from backend.jobs.event_bus import event_bus
from datetime import datetime, UTC, timedelta
from threading import Event
from dataclasses import field
from typing import Any
import logging

logger = logging.getLogger(__name__)

class Pipeline:
    """
    Orchestrates end-to-end workflows.
    """

    def __init__(self,
                 slot_service : SlotService,
                 metadata_service : MetadataService,
                 download_service : DownloadFileService,
                 process_service : ProcessFileService):
        
        self.slot_service = slot_service
        self.metadata_service = metadata_service
        self.download_service = download_service
        self.process_service = process_service
    
    def sync_slots(self, 
                   cancel_event: Event,
                   job_id: str,
                   job_type: JobType) -> SyncSlotsResult:
        """
        Syncs slots from remote source
        """
        logger.info("Slot sync pipeline started")
        try:
            slots_synced = self.slot_service.sync_slots(cancel_event)
            
            self.publish_job_event(job_id, job_type, JobEventType.SLOTS_SYNCED , {"slots_synced":slots_synced})
            logger.info(
                "Slot sync pipeline completed",
                extra={"slots_synced": slots_synced}
            )
            return SyncSlotsResult(
                slots_synced
            )
        
        except CancelledError:
            logger.info("Slot sync pipeline cancelled")
            raise

        except Exception:
            logger.exception("Slot sync pipeline failed")
            raise
    
    def get_active_slot(self) -> SlotResult:
        """
        Get details of active slot if present
        """
        logger.info("Get active slot pipeline started")
        try:
            active_slot = self.slot_service.get_active_slot()
            
            if active_slot:
                logger.info(
                    "Active slot found",
                    extra={"start": active_slot.bot_utc, 
                           "end": active_slot.eot_utc}
                )
            else:
                logger.info("No active slot found")
            
            return SlotResult(
                start=active_slot.bot_utc if active_slot else None,
                end=active_slot.eot_utc if active_slot else None
            )
        except Exception:
            logger.exception("Get active slot pipeline failed")
            raise
    
    def get_next_active_slot(self) -> SlotResult:
        """
        Get details of next active slot if present
        """
        logger.info("Get next active slot pipeline started")
        try:
            next_active_slot = self.slot_service.get_next_active_slot()
            
            if next_active_slot:
                logger.info(
                    "Next active slot found",
                    extra={"start": next_active_slot.bot_utc, 
                           "end": next_active_slot.eot_utc}
                )
            else:
                logger.info("No next active slot found")
            
            return SlotResult(
                start=next_active_slot.bot_utc if next_active_slot else None,
                end=next_active_slot.eot_utc if next_active_slot else None
            )
        except Exception:
            logger.exception("Get next active slot pipeline failed")
            raise
    
    def run_ingestion_cycle(self, 
                            instrument: Instrument, 
                            cancel_event: Event,
                            job_id: str,
                            job_type: str) -> RunIngestionCycleResult:
        """
        Syncs metadata and download files as they get available
        based on active slot.
        Decide next run dynamically.

        :param instrument: Observation Instrument of our interest.
        :return: RunIngestionCycleResult model containing files metadata
        synced, number of files downloaded and in how much time to do
        the next run.
        """
        logger.info(
            "Ingestion cycle execution started",
            extra={"instrument":instrument}
        )
        try:
            now = datetime.now(UTC)
            
            slot = self.slot_service.get_active_slot()
            self.publish_job_event(job_id, job_type, JobEventType.SLOT_ACTIVE, {"active slot": slot is not None})

            if not slot:
                next_run = self.slot_service.next_active_slot_in()
                logger.info(
                    "No active slot found",
                    extra={
                        "next_run": str(next_run) if next_run else None
                    }
                )
                return RunIngestionCycleResult(
                    0,
                    0,
                    next_run
                )
            if cancel_event and cancel_event.is_set():
                raise CancelledError()
            
            metadata_synced = self.metadata_service.sync_metadata_by_slots(instrument, [slot], cancel_event)
            self.publish_job_event(job_id, job_type, JobEventType.METADATA_SYNCED, {"metadata_synced": metadata_synced})

            self.download_service.recover_stale_files(now, instrument)
            self.publish_job_event(job_id, job_type, JobEventType.DOWNLOAD_RECOVER)

            if cancel_event and cancel_event.is_set():
                raise CancelledError()
            
            downloaded = self.download_service.download_files_by_slots(instrument, [slot], cancel_event)
            self.publish_job_event(job_id, job_type, JobEventType.DOWNLOAD_COMPLETED, {"downloaded": downloaded})

            logger.info(
                "Ingestion cycle execution completed",
                extra={
                    "metadata_synced": metadata_synced,
                    "downloaded":downloaded
                }
            )

            return RunIngestionCycleResult(
                metadata_synced,
                downloaded,
                timedelta(minutes=5)
            )
        except CancelledError:
            logger.info("Ingestion cycle execution cancelled")
            raise
        except Exception:
            logger.exception("Ingestion cycle execution failed")
            raise
    
    def get_processed_frames(self,
                             instrument: Instrument,
                             observation_start_utc: str,
                             observation_end_utc: str,
                             limit: int,
                             offset: int) -> GetProcessedFramesResult:
        """
        returns processedfiles for a given observation time period and instrument.

        :param instrument: instrument used for observation
        :param observation_start_utc: observation start time
        :param observation_end_utc: observation end time
        :param limit:
        :param offset:
        :return: domain entity with `processed_files` containing list of processed
        file domain entities. 
        """
        logger.info(
            "Processed frames retrieval pipeline started",
            extra={
                "instrument":instrument,
                "observation_start_utc":observation_start_utc,
                "observation_end_utc":observation_end_utc
            }
        )
        try:
            observation_start_dt = parse_utc_datetime(observation_start_utc)
            observation_end_dt = parse_utc_datetime(observation_end_utc)

            processed_files, total = self.process_service.get_files_by_observation_and_status(
                instrument, 
                FileStatus.PROCESSED, 
                observation_start_dt, 
                observation_end_dt,
                limit,
                offset
            )
            logger.info(
                "Processed frames retrieval pipeline completed",
                extra={
                    "count":len(processed_files)
                }
            )
            return GetProcessedFramesResult(
                processed_files=processed_files,
                total=total,
                limit=limit,
                offset=offset
            )
        
        except Exception:
            logger.exception("Processed frames retrieval pipeline failed")
            raise
    
    def sync_processed_frames(self,
                             instrument: Instrument,
                             observation_start_utc: str,
                             observation_end_utc: str,
                             cancel_event: Event,
                             job_id: str,
                             job_type: JobType) -> SyncProcessedFramesResult:
        """
        User driven observation based pipeline.
        returns detials of operation done for syncing processed frames for a given 
        observation instrument and time period 

        :param instrument: instrument used for observation
        :param observation_start_utc: observation start time
        :param observation_end_utc: observation end time
        :param cancel_event: to track cancellation trigger for terminating the job
        :return: dictionary containing key-value pairs for metadata synced, files downloaded, 
        marked ready and processed. 
        """
        logger.info(
            "Processed frames sync pipeline started",
            extra={
                "instrument":instrument,
                "observation_start_utc":observation_start_utc,
                "observation_end_utc":observation_end_utc
            }
        )
        try:
            observation_start_dt = parse_utc_datetime(observation_start_utc)
            observation_end_dt = parse_utc_datetime(observation_end_utc)
            now_utc = datetime.now(UTC)

            padded_start = observation_start_dt - timedelta(hours=12)
            padded_end = min(observation_end_dt + timedelta(hours=12), now_utc)

            metadata_synced = self.metadata_service.sync_metadata(
                instrument=instrument,
                cancel_event=cancel_event,
                downlink_start_utc=padded_start,
                downlink_end_utc=padded_end,
            )
            self.publish_job_event(job_id, job_type, JobEventType.METADATA_SYNCED, {"metadata_synced":metadata_synced})

            if cancel_event and cancel_event.is_set():
                raise CancelledError()

            self.download_service.recover_stale_files(now_utc, instrument)
            self.publish_job_event(job_id, job_type, JobEventType.DOWNLOAD_RECOVER)

            downloaded = self.download_service.download_files_by_observation(instrument,observation_start_dt,observation_end_dt, cancel_event)
            self.publish_job_event(job_id, job_type, JobEventType.DOWNLOAD_COMPLETED, {"downloaded":downloaded})

            if cancel_event and cancel_event.is_set():
                raise CancelledError()

            self.process_service.recover_stale_files(now_utc, instrument)
            self.publish_job_event(job_id, job_type, JobEventType.PROCESS_RECOVER)

            marked_ready = self.process_service.mark_ready_files_for_processing(instrument, observation_start_dt, observation_end_dt, cancel_event)
            self.publish_job_event(job_id, job_type, JobEventType.PROCESS_READY, {"marked_ready":marked_ready})
            
            if cancel_event and cancel_event.is_set():
                raise CancelledError()

            processed = self.process_service.process_pending_files(instrument, observation_start_dt, observation_end_dt, cancel_event)
            self.publish_job_event(job_id, job_type, JobEventType.PROCESS_COMPLETED, {"processed":processed})
            
            logger.info(
                "Processed frames sync pipeline completed",
                extra={
                    "metadata_synced": metadata_synced,
                    "downloaded": downloaded,
                    "marked_ready": marked_ready,
                    "processed": processed
                }
            )

            return SyncProcessedFramesResult(
                metadata_synced,
                downloaded,
                marked_ready,
                processed
            )
        
        except CancelledError:
            logger.info("Processed frame sync pipeline cancelled")
            raise

        except Exception:
            logger.exception("Processed frames sync pipeline failed")
            raise
    
    def publish_job_event(
        self,
        job_id: str,
        job_type: str,
        event_name: JobEventType,
        data: dict[str, Any] | None = None
    ) -> None:
        """
        Publish standardized pipeline job event.
        """

        event_bus.publish(
            job_id=job_id,
            event=JobEvent(
                job_id=job_id,
                job_type=job_type,
                job_status=JobStatus.RUNNING,
                event=event_name,
                data=data or {}
            )
        )