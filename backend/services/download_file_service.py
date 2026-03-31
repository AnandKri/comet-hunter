from pathlib import Path
from typing import List, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.domain.processed_file import ProcessedFile
from backend.util.enums import FileStatus

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
                 download_directory: Path,
                 max_workers: int = 4):
        self._processed_repository = processed_repository
        self._download_directory = download_directory
        self._max_workers = max_workers
    
    def download_pending_files(self) -> int:
        """
        Entry workflow for downloading eligible files.

        :return: returns number of files downloaded.
        """

        files = self._get_files_to_download()

        if not files:
            return 0
        
        return self._parallel_download(files)
    
    def _get_files_to_download(self) -> List[ProcessedFile]:
        """
        Fetch files eligible for download or retry

        :return: Files needing download
        """

        retryable = self._processed_repository.get_retryable_downloads()

        # add repo method to get list of files need to be downloaded

        return retryable
    
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
        :return: Ture if file is successfully downloaded. False otherwise
        """

        try:
            file = file.transition_to(FileStatus.DOWNLOADING)
            self._processed_repository.save(file)
            url = self._build_download_url(file)
            local_path = self._download_directory / file.raw_file_name
            self._download(url, local_path)
            file = file.transition_to(FileStatus.DOWNLOADED)
            file = file.__class__(
                **{**file.__dict__,
                   "downloaded_at":"datetime('now')"}
            )
            self._processed_repository.save(file)
            return True
        except Exception as e:
            file = file.transition_to(FileStatus.DOWNLOADING_FAILED)
            file = file.__class__(
                **{**file.__dict__,
                   "error_message":str(e)}
            )
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
    
    def _build_download_url(self, file: ProcessedFile) -> str:
        """
        Constructs remote file URL.

        :param file: Target file
        :return: Download URL
        """

        # implement based on metadata source
        raise NotImplementedError