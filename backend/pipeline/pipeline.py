from backend.services.slot_service import SlotService
from backend.services.metadata_service import MetadataService
from backend.services.download_file_service import DownloadFileService
from backend.services.process_file_service import ProcessFileService
from backend.util.enums import Instrument, FileStatus
from backend.pipeline.models import RunIngestionCycleResult, GetProcessedFramesResult, SyncProcessedFramesResult, SyncSlotsResult, SlotResult
from backend.util.funcs import parse_utc_datetime
from backend.jobs.exceptions import CancelledError
from datetime import datetime, UTC, timedelta
from threading import Event
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
    
    def sync_slots(self, cancel_event: Event) -> SyncSlotsResult:
        """
        Syncs slots from remote source
        """
        logger.info("Slot sync pipeline started")
        try:
            slots_synced = self.slot_service.sync_slots()
            logger.info(
                "Slot sync pipeline completed",
                extra={"slots_synced": slots_synced}
            )
            return SyncSlotsResult(
                slots_synced
            )
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
    
    def run_ingestion_cycle(self, instrument: Instrument) -> RunIngestionCycleResult:
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
            
            metadata_synced = self.metadata_service.sync_metadata_by_slots(instrument, [slot])

            self.download_service.recover_stale_files(now, instrument)
            downloaded = self.download_service.download_files_by_slots(instrument, [slot])

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
        except Exception:
            logger.exception("Ingestion cycle execution failed")
            raise
    
    def get_processed_frames(self,
                             instrument: Instrument,
                             observation_start_utc: str,
                             observation_end_utc: str,
                             cancel_event: Event) -> GetProcessedFramesResult:
        """
        returns processedfiles for a given observation time period and instrument.

        :param instrument: instrument used for observation
        :param observation_start_utc: observation start time
        :param observation_end_utc: observation end time
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

            processed_files = self.process_service.get_files_by_observation_and_status(
                instrument, 
                FileStatus.PROCESSED, 
                observation_start_dt, 
                observation_end_dt
            )
            logger.info(
                "Processed frames retrieval pipeline completed",
                extra={
                    "count":len(processed_files)
                }
            )
            return GetProcessedFramesResult(
                processed_files=processed_files
            )
        except Exception:
            logger.exception("Processed frames retrieval pipeline failed")
            raise
    
    def sync_processed_frames(self,
                             instrument: Instrument,
                             observation_start_utc: str,
                             observation_end_utc: str,
                             cancel_event: Event) -> SyncProcessedFramesResult:
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

            metadata_synced = self.metadata_service.sync_metadata(instrument,padded_start,padded_end)

            if cancel_event and cancel_event.is_set():
                raise CancelledError()

            self.download_service.recover_stale_files(now_utc, instrument)
            downloaded = self.download_service.download_files_by_observation(instrument,observation_start_dt,observation_end_dt)

            if cancel_event and cancel_event.is_set():
                raise CancelledError()

            self.process_service.recover_stale_files(now_utc, instrument)
            marked_ready = self.process_service.mark_ready_files_for_processing(instrument, observation_start_dt, observation_end_dt)
            
            if cancel_event and cancel_event.is_set():
                raise CancelledError()

            processed = self.process_service.process_pending_files(instrument, observation_start_dt, observation_end_dt)
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
        except Exception:
            logger.exception("Processed frames sync pipeline failed")
            raise