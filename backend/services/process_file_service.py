from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.domain.processed_file import ProcessedFile
from backend.util.enums import FileStatus
from dataclasses import replace
from datetime import datetime

class ProcessFileService:
    """
    Service responsible for:
    - Identifying files that are ready to be processed
    - processing files
    - updating lifecycle states
    - managing processing retries
    """

    def __init__(self, 
                 processed_repository: ProcessedFileRepository,
                 processed_directory: Path,
                 max_workers: int = 4):
        self._processed_repository = processed_repository
        self._processed_directory = processed_directory
        self._max_workers = max_workers
    
    def process_pending_files(self) -> int:
        """
        Entry workflow for processing eligible files.
        
        :return: returns number of files processed
        """

        files = self._get_files_to_process()

        if not files:
            return 0
        
        return self._parallel_process(files)
    
    def _get_files_to_process(self) -> List[ProcessedFile]:
        """
        Fetch files eligible for process or retry

        :return: Files needing process
        """

        ready = self._processed_repository.get_ready_files()

        retryable = self._processed_repository.get_retryable_process()
        
        return ready + retryable
    
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