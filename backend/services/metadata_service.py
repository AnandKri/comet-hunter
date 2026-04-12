from typing import List
import requests
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.domain.file_metadata import FileMetadata
from backend.util.constants import Url
from backend.util.enums import Instrument
from datetime import datetime, timedelta

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
    
    def sync_metadata(self, instrument: Instrument, since: str, now: str) -> int:
        """
        Fetch metadata from remote source and update database
        
        :param instrument: instrument to sync (C2/C3)
        :param since: start datetime (ISO string)
        :param now: end datetime (ISO string)
        :return: number of new records inserted
        """

        all_metadata = []

        for raw_text in self._fetch_metadata(instrument, since, now):
            parsed = self._parse_metadata(raw_text)
            all_metadata.extend(parsed)

        new_files = self._discover_new_files(all_metadata)

        return self._metadata_repository.bulk_create_metadata(new_files)
    
    def _fetch_metadata(self, instrument: Instrument, since: str, now: str) -> List[str]:
        """
        Fetch metadata for each day in a given range.

        :param instrument: instrument (C2/C3)
        :param since: start datetime (ISO string)
        :param now: end datetime (ISO string), supposed to be current datetime
        :return: list of raw metadata text (one per day)
        """

        since_date = datetime.fromisoformat(since).date()
        now_date = datetime.fromisoformat(now).date()
        current = since_date

        results = []

        while current <= now_date:
            
            dt_str = current.isoformat()
            url = Url.build_metadata_url(dt_str, instrument)

            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                results.append(response.text)
            except Exception:
                continue

            current += timedelta(days=1)

        return results
    
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
    
    def _parse_metadata(self, raw_text: str) -> List[FileMetadata]:
        """
        Parse metadata text into domain objects.

        :param raw_text: Raw metadata content
        :return: List of FileMetadata domain entities
        """

        files = []
        lines = raw_text.strip().splitlines()

        for line in lines:
            if not line.strip():
                continue

            parts = line.split()

            try:
                filename = parts[0]
                date_part = parts[1]
                time_part = parts[2]
                dt_str = f"{date_part} {time_part}"
                dt_iso = datetime.strptime(dt_str, "%Y/%m/%d %H:%M:%S").isoformat()
                instrument = Instrument(parts[3].lower())
                exposure = float(parts[4])
                width = int(parts[5])
                height = int(parts[6])
                roll = float(parts[-2])
                
                files.append(
                    FileMetadata(
                        raw_file_name=filename,
                        raw_file_hash=None,
                        datetime_of_observation=dt_iso,
                        instrument=instrument,
                        exposure_time=exposure,
                        width=width,
                        height=height,
                        roll=roll
                    )
                )

            except Exception:
                continue
        
        return files