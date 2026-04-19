from pathlib import Path
from typing import List, Optional
from dataclasses import replace
import requests
from datetime import datetime, UTC
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.domain.processed_file import ProcessedFile
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.database.domain.file_metadata import FileMetadata
from backend.util.enums import FileStatus, Instrument
from backend.util.constants import Url
from backend.util.funcs import validate_time_window
from backend.services.metadata_service import MetadataService

class DownloadFileService:
    """
    Service responsible for:
    - Identifying files that need downloading
    - downloading raw files
    - updating lifecycle states
    - managing download retries
    """

    def __init__(self, 
                 processed_repository: ProcessedFileRepository,
                 metadata_service: MetadataService,
                 download_directory: Path,
                 max_workers: int = 4):
        self._processed_repository = processed_repository
        self._metadata_service = metadata_service
        self._download_directory = download_directory
        self._max_workers = max_workers
    
    def download_files_for_slots(self, instrument: Instrument, slots: List[DownlinkSlot]) -> int:
        """
        Downloads files corresponding to slots and given instrument.

        - fetch metadata for slot range
        - identify potential files for download
        - identify eligible files for download (retry + new)
        - perform parallel download
        
        :param instrument: instrument used for obsersation
        :param slots: list of slot domain entities
        :return: returns number of successfully downloaded files.
        """

        if not slots:
            return 0
        
        downlink_start_utc = min(slot.bot_utc for slot in slots)
        downlink_end_utc = max(slot.eot_utc for slot in slots)

        metadata_files = self._metadata_service.get_metadata_for_downlink(instrument, downlink_start_utc, downlink_end_utc)

        files = self._get_files_to_download(metadata_files)
        if not files:
            return 0
        
        return self._parallel_download(files)
    
    def download_files_for_downlink(self, instrument: Instrument, downlink_start_utc: str, downlink_end_utc: str) -> int:
        """
        Download files within a given downlink time frame and instrument.

        :param instrument: Instrument used for observation
        :param downlink_start_utc: start timestamp (ISO)
        :param downlink_end_utc: end timestamp (ISO)
        :return: number of files downloaded successfully.
        """

        validate_time_window(downlink_start_utc, downlink_end_utc)

        metadata_files = self._metadata_service.get_metadata_for_downlink(instrument, downlink_start_utc, downlink_end_utc)

        files = self._get_files_to_download(metadata_files)
        if not files:
            return 0
        
        return self._parallel_download(files)
    
    def download_files_for_observation(self, instrument: Instrument, observation_start_utc: str, observation_end_utc: str) -> int:
        """
        download files within an observation time period and instrument.

        :param instrument: Instrument used for observation
        :param observation_start_utc: start timestamp (ISO)
        :param observation_end_utc: end timestamp (ISO)
        :return: number of files downloaded successfully.
        """

        validate_time_window(observation_start_utc, observation_end_utc)

        metadata_files = self._metadata_service.get_metadata_for_observation(instrument, observation_start_utc, observation_end_utc)

        files = self._get_files_to_download(metadata_files)
        if not files:
            return 0
        
        return self._parallel_download(files)
    
    def get_downloaded_files_by_time(self, instrument: Instrument, download_start_utc: str, download_end_utc: str) -> list[ProcessedFile]:
        """
        returns downloaded files between a time window

        :param instrument: instrument used for observation
        :param download_start_utc: start timestamp (ISO)
        :param download_end_utc: end timestamp (ISO)
        :return: list of process file entities
        """

        validate_time_window(download_start_utc, download_end_utc)

        return self._processed_repository.get_downloaded_files_by_time(instrument, download_start_utc, download_end_utc)
    
    def _get_files_to_download(self, metadata_files: List[FileMetadata]) -> List[ProcessedFile]:
        """
        Convert metadata into ProcessedFile entities and filter
        eligible files for download

        Includes:
            - new files (not in DB)
            - retryable failed downloads
        
        :param metadata_files: metadata entities
        :return: ProcessedFiles entities ready for download
        """

        files : List[ProcessedFile] = []

        for metadata in metadata_files:
            existing = self._processed_repository.exists_by_name(metadata.raw_file_name)

            if not existing:
                file = ProcessedFile(
                    raw_file_name=metadata.raw_file_name,
                    raw_file_hash=None,
                    raw_file_path=str(self._download_directory / metadata.raw_file_name),
                    raw_file_size=None,
                    processed_file_name=None,
                    processed_file_hash=None,
                    processed_file_path=None,
                    processed_file_size=None,
                    datetime_of_observation=metadata.datetime_of_observation,
                    instrument=metadata.instrument,
                    status=FileStatus.DISCOVERED,
                    error_message=None,
                    downloaded_at=None,
                    last_downloading_attempt_at=None,
                    downloading_attempt_count=0,
                    processed_at=None,
                    last_processing_attempt_at=None,
                    processing_attempt_count=0
                )

                self._processed_repository.create_file(**file.__dict__)
                files.append(file)
            
            else:
                file = self._processed_repository.read_file_by_name(metadata.raw_file_name)
                if file.can_retry_downloading(self._processed_repository.max_downloading_attempts):
                    files.append(file)
        
        return files
    
    def _parallel_download(self, files: List[ProcessedFile]) -> int:
        """
        Download files concurrently

        :param files: Files to download
        :return: number of successful downloads
        """

        success = 0

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(self._download_single, file)
                for file in files
            ]

            for future in as_completed(futures):
                if future.result():
                    success += 1
        
        return success
    
    def _download_single(self, file: ProcessedFile) -> bool:
        """
        Downloads one file and updates lifecycle

        :param file: File to be downloaded
        :return: True if file is successfully downloaded. False otherwise
        """

        if not file.datetime_of_observation:
            return False

        try:
            file = file.transition_to(FileStatus.DOWNLOADING)
            self._processed_repository.save(file)
            obs_date = datetime.fromisoformat(
                file.datetime_of_observation
                ).date().isoformat()
            download_url = Url.build_fits_url(dt=obs_date, 
                                     instrument=file.instrument,
                                     filename=file.raw_file_name)
            
            local_path = file.raw_file_path
            self._download(download_url, local_path)
            file = file.transition_to(FileStatus.DOWNLOADED)
            file = replace(file, downloaded_at=datetime.now(UTC).isoformat())
            self._processed_repository.save(file)
            
            return True
        
        except Exception as e:
            file = file.transition_to(FileStatus.DOWNLOADING_FAILED)
            file = replace(file,
                           error_message=str(e),
                           last_downloading_attempt_at = datetime.now(UTC).isoformat(),
                           downloading_attempt_count = file.downloading_attempt_count + 1)
            
            self._processed_repository.save(file)
            return False
    
    def _download(self, url: str, path: Path) -> None:
        """
        Performs actual file download.

        Parameters:
            url: Remote file URL
            path: Local destination
        """

        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(path, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)