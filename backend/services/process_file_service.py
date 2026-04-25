from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.domain.processed_file import ProcessedFile
from backend.util.enums import FileStatus, Instrument
from backend.util.funcs import validate_time_window
from dataclasses import replace
from datetime import datetime, timedelta

class ProcessFileService:
    """
    Service responsible for:
    - Identifying files that are ready to be processed
    - processing files
    - updating lifecycle states
    - managing processing retries
    """

    LOOKBACK_BUFFER = timedelta(hours=1)
    MIN_OBSERVATION_GAP = timedelta(minutes=8)
    MAX_OBSERVATION_GAP = timedelta(minutes=16)
    PROCESSING_TIMEOUT = timedelta(minutes=5)

    def __init__(self, 
                 processed_repository: ProcessedFileRepository,
                 processed_directory: Path,
                 max_workers: int = 4):
        self._processed_repository = processed_repository
        self._processed_directory = processed_directory
        self._max_workers = max_workers
    
    def recover_stale_files(self, now_utc: str, instrument: Instrument) -> int:
        """
        Recovers files stuck in intermediate states `PROCESSING`
        by marking them as failed if they exceed allowed timeout.

        :param now_utc: current UTC timestamp (ISO format)
        :return: number of files recovered.
        """

        now_dt = datetime.fromisoformat(now_utc)

        recovered_count = 0

        processing_files = self._processed_repository.get_files_by_status(instrument, status=FileStatus.PROCESSING, order_by='last_processing_attempt_at')

        for file in processing_files:
            if not file.last_processing_attempt_at:
                continue
            last_attempt_dt = datetime.fromisoformat(file.last_processing_attempt_at)
            if now_dt - last_attempt_dt > self.PROCESSING_TIMEOUT:
                try:
                    updated = file.transition_to(FileStatus.PROCESSING_FAILED)
                    updated = replace(
                        updated,
                        error_message="Recovered: processing timeout",
                        processing_attempt_count=file.processing_attempt_count + 1,
                        last_processing_attempt_at=now_utc
                    )
                    if self._processed_repository.save(updated):
                        recovered_count += 1
                except ValueError:
                    pass
        
        return recovered_count
    
    def recover_unmarked_ready_files(self,instrument: Instrument,observation_start_utc: str,observation_end_utc: str) -> int:
        """
        Recovers files that are in DOWNLOADED state but were not marked as READY
        due to missed or skipped execution of the pairing logic.

        This method re-applies the READY-marking algorithm over the given
        observation window (with internal lookback buffer), ensuring that
        any eligible files are transitioned to READY.

        It is idempotent:
        - Files already in READY/PROCESSED are not modified
        - Only valid transitions are applied

        Intended usage:
        - After crashes
        - After logic changes
        - As a periodic consistency check in the pipeline

        :param instrument: Instrument used for observation
        :param observation_start_utc: Start of observation window (ISO UTC string)
        :param observation_end_utc: End of observation window (ISO UTC string)
        :return: Number of files transitioned to READY
        """
        
        return self.mark_ready_files_for_processing(
            instrument=instrument,
            observation_start_utc=observation_start_utc,
            observation_end_utc=observation_end_utc
        )

    def mark_ready_files_for_processing(self, instrument: Instrument, observation_start_utc: str, observation_end_utc: str) -> int:
        """
        Goes through all the files for a given observation time period and instrument, 
        updates relevant files' status as `READY`.

        :param instrument: Instrument used for observation
        :param observation_start_utc: starting utc timestamp of observation
        :param observation_end_utc: ending utc timestamp of observation
        :return: Number of files which are updated to `READY`
        """

        validate_time_window(observation_start_utc, observation_end_utc)
        
        observation_start_datetime = datetime.fromisoformat(observation_start_utc)
        fetch_start_time = (observation_start_datetime - self.LOOKBACK_BUFFER).isoformat()

        files: List[ProcessedFile] = self._processed_repository.get_files_by_observation(
            instrument, 
            fetch_start_time,
            observation_end_utc
        )

        prev = None
        updated_count = 0
        for file in files:
            file_observation_datetime = datetime.fromisoformat(file.datetime_of_observation)
            if (file_observation_datetime >= observation_start_datetime) and (file.status == FileStatus.DOWNLOADED):
                if prev:
                    observation_difference = file_observation_datetime - prev_observation_datetime
                    if  self.MIN_OBSERVATION_GAP <= observation_difference <= self.MAX_OBSERVATION_GAP:
                        try:
                            updated_file = file.transition_to(FileStatus.READY)
                            updated_file = replace(
                                updated_file,
                                previous_file_name=prev.raw_file_name
                            )
                            if self._processed_repository.save(updated_file):
                                updated_count += 1
                        except ValueError:
                            pass
            if file.status in [FileStatus.DOWNLOADED, FileStatus.PROCESSED, FileStatus.READY]:
                prev = file
                prev_observation_datetime = file_observation_datetime
        return updated_count

    def process_pending_files(self, instrument: Instrument, observation_start_utc: str, observation_end_utc: str) -> int:
        """
        Entry workflow for processing eligible files.
        
        :param instrument: Instrument used for observation
        :param observation_start_utc: starting utc timestamp of observation
        :param observation_end_utc: ending utc timestamp of observation
        :return: returns number of files processed
        """

        validate_time_window(observation_start_utc, observation_end_utc)

        files = self._get_files_to_process(instrument, observation_start_utc, observation_end_utc)

        if not files:
            return 0
        
        return self._parallel_process(files)
    
    def _get_files_to_process(self, instrument: Instrument, observation_start_utc: str, observation_end_utc: str) -> List[ProcessedFile]:
        """
        Fetch files which are `READY` or eligible for retrying processing

        :param instrument: Instrument used for observation
        :param observation_start_utc: starting utc timestamp of observation
        :param observation_end_utc: ending utc timestamp of observation
        :return: Files needing process
        """

        validate_time_window(observation_start_utc, observation_end_utc)        

        ready = self._processed_repository.get_files_by_observation_and_status(
            instrument, 
            FileStatus.READY, 
            observation_start_utc,
            observation_end_utc
        )

        retryable = self._processed_repository.get_files_by_observation_and_status(
            instrument,
            FileStatus.PROCESSING_FAILED,
            observation_start_utc,
            observation_end_utc
            )

        retryable = [
            file for file in retryable
            if file.can_retry_processing(self._processed_repository.max_processing_attempts)
        ]
        
        return list({f.raw_file_name: f for f in (ready + retryable)}.values())
    
    def _parallel_process(self, files: List[ProcessedFile]) -> int:
        """
        Process files concurrently

        :param files: Files to process
        :return: number of successful processes
        """

        success = 0

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(self._process_single, file)
                for file in files
            ]

            for future in as_completed(futures):
                if future.result():
                    success += 1
        
        return success
    
    def _process_single(self, file: ProcessedFile) -> bool:
        """
        Processes one file and updates lifecycle

        :param file: File to be processed
        :return: True if file is successfully processed. False otherwise
        """

        try:
            file = file.transition_to(FileStatus.PROCESSING)
            file = replace(file,
                           last_processing_attempt_at=datetime.utcnow().isoformat())
            self._processed_repository.save(file)
            local_path = self._processed_directory / file.raw_file_name
            self._process(local_path)
            file = file.transition_to(FileStatus.PROCESSED)
            file = replace(file, processed_at=datetime.utcnow().isoformat())
            self._processed_repository.save(file)
            return True
        except Exception as e:
            file = file.transition_to(FileStatus.PROCESSING_FAILED)
            file = replace(file, 
                           error_message=str(e),
                           last_processing_attempt_at=datetime.utcnow().isoformat(),
                           processing_attempt_count=file.processing_attempt_count + 1)
            self._processed_repository.save(file)
            return False
    
    def _process(self, processed_path: Path) -> None:
        """
        Performs actual file process.

        Parameters:
            processed_path: processed file path
        """

        # implement processing logic - utilize file.raw_file_path

        raise NotImplementedError