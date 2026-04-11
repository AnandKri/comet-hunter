from typing import List
import requests
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.domain.file_metadata import FileMetadata
from backend.util.constants import Url

class MetadataService:
    """
    Service responsible for:
    - Fetching metadata from remote source
    - Parsing metadata
    - Discovering new files
    - Persisting metadata into database
    """

    def __init__(self, metadata_repository: FileMetadataRepository):
        self._metadata_repository = metadata_repository
    
    def sync_metadata(self) -> int:
        """
        Fetch metadata from remote source and update database

        :return: number of new files metadata inserted
        """

        raw_data = self._fetch_metadata()
        files_metadata = self._parse_metadata(raw_data)
        new_files_metadata = self._discover_new_files(files_metadata)
        
        return self._metadata_repository.bulk_create_metadata(new_files_metadata)
    
    def _fetch_metadata(self) -> str:
        """
        Fetch metadata.

        :return: Raw metadata text
        """

        response = requests.get(Url.METADATA, timeout=30)
        response.raise_for_status()

        return response.text
    
    def _parse_metadata(self, raw_text: str) -> List[FileMetadata]:
        """
        Parse metadata text into domain objects.

        :param raw_text: Raw metadata content
        :return: List of FileMetadata domain entities
        """

        # implement parsing logic
        raise NotImplementedError
    
    def _discover_new_files(self, files:List[FileMetadata]) -> List[FileMetadata]:
        """
        Filters only new files not present in DB

        :param files: Parsed metadata records
        :return: Newly discovered files
        """

        new_files = []

        for file in files:
            if not self._metadata_repository.exists_by_filename(file.raw_file_name):
                new_files.append(file)
        
        return new_files