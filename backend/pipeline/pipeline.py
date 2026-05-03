from backend.services.slot_service import SlotService
from backend.services.metadata_service import MetadataService
from backend.services.download_file_service import DownloadFileService
from backend.services.process_file_service import ProcessFileService
from backend.util.enums import Instrument, FileStatus
from backend.pipeline.models import RunLivePipelineResult, GetProcessedFramesResult, SyncProcessedFramesResult, SyncSlotsResult
from backend.util.funcs import _to_utc
from datetime import datetime, UTC, timedelta

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
    
    def sync_slots(self) -> SyncSlotsResult:
        """
        Syncs slots from remote source
        """
        slots_synced = self.slot_service.sync_slots()
        return SyncSlotsResult(
            slots_synced
        )
    
    def run_live_pipeline(self, instrument: Instrument) -> RunLivePipelineResult:
        """
        Syncs metadata and download files as they get available
        based on active slot.
        Decide next run dynamically.

        :param instrument: Observation Instrument of our interest.
        :return: RunLivePipelineResult model containing files metadata
        synced, number of files downloaded and in how much time to do
        the next run.
        """

        now = datetime.now(UTC).isoformat()
        
        slot = self.slot_service.sync_and_get_active_slot()
        if not slot:
            next_run = self.slot_service.next_active_slot_in()
            return RunLivePipelineResult(
                0,
                0,
                next_run
            )
        
        metadata_synced = self.metadata_service.sync_metadata_by_slots(instrument, [slot])

        self.download_service.recover_stale_files(now, instrument)
        downloaded = self.download_service.download_files_by_slots(instrument, [slot])

        return RunLivePipelineResult(
            metadata_synced,
            downloaded,
            timedelta(minutes=5)
        )
    
    def get_processed_frames(self,
                             instrument: Instrument,
                             observation_start_utc: str,
                             observation_end_utc: str) -> GetProcessedFramesResult:
        """
        returns processedfiles for a given observation time period and instrument.

        :param instrument: instrument used for observation
        :param observation_start_utc: observation start time
        :param observation_end_utc: observation end time
        :return: domain entity with `processed_files` containing list of processed
        file domain entities. 
        """
        processed_files = self.process_service.get_files_by_observation_and_status(instrument, 
                                                                                   FileStatus.PROCESSED, 
                                                                                   observation_start_utc, 
                                                                                   observation_end_utc)
        
        return GetProcessedFramesResult(
            processed_files=processed_files
        )

    
    def sync_processed_frames(self,
                             instrument: Instrument,
                             observation_start_utc: str,
                             observation_end_utc: str) -> SyncProcessedFramesResult:
        """
        User driven observation based pipeline.
        returns detials of operation done for syncing processed frames for a given 
        observation instrument and time period 

        :param instrument: instrument used for observation
        :param observation_start_utc: observation start time
        :param observation_end_utc: observation end time
        :return: dictionary containing key-value pairs for metadata synced, files downloaded, 
        marked ready and processed. 
        """
        
        obs_start_dt = _to_utc(observation_start_utc)
        obs_end_dt = _to_utc(observation_end_utc)
        now_utc = datetime.now(UTC).isoformat()

        padded_start = (obs_start_dt - timedelta(hours=12)).isoformat()
        padded_end = min(obs_end_dt + timedelta(hours=12),now_utc).isoformat()

        metadata_synced = self.metadata_service.sync_metadata(instrument,padded_start,padded_end)

        self.download_service.recover_stale_files(now_utc, instrument)
        downloaded = self.download_service.download_files_by_observation(instrument,observation_start_utc,observation_end_utc)

        self.process_service.recover_stale_files(now_utc, instrument)
        marked_ready = self.process_service.mark_ready_files_for_processing(instrument, observation_start_utc, observation_end_utc)
        processed = self.process_service.process_pending_files(instrument, observation_start_utc, observation_end_utc)

        return SyncProcessedFramesResult(
            metadata_synced,
            downloaded,
            marked_ready,
            processed
        )