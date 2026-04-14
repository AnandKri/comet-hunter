from typing import List, Optional
import requests
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.domain.file_metadata import FileMetadata
from backend.util.constants import Url
from backend.util.enums import Instrument
from datetime import datetime, timedelta, UTC
from zoneinfo import ZoneInfo
import re

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
    
    def sync_metadata(self, instrument: Instrument, since: Optional[str] = None, now: Optional[str] = None) -> int:
        """
        Fetch metadata from remote source and update database.

        If `since` is not provided, it is inferred from DB (latest available record).
        If `now` is not provided, current UTC time is used.

        :param instrument: instrument to sync (C2/C3)
        :param since: start datetime (ISO string, optional)
        :param now: end datetime (ISO string, optional)
        :return: number of new records inserted
        """

        if now is None:
            now = datetime.now(UTC).isoformat()
        if since is None:
            since = self._metadata_repository.get_latest_last_modified(instrument)
            if since is None:
                since = (datetime.fromisoformat(now) - timedelta(days=1)).isoformat()
            else:
                since = (datetime.fromisoformat(since) - timedelta(days=1)).isoformat()

        all_metadata = []

        print(since, now)

        for raw_text, last_modified_map in self._fetch_metadata(instrument, since, now):
            parsed = self._parse_metadata(raw_text, last_modified_map)
            all_metadata.extend(parsed)
        
        new_files = self._discover_new_files(all_metadata)

        return self._metadata_repository.bulk_create_metadata(new_files)
    
    def _fetch_metadata(self, instrument: Instrument, since: str, now: str) -> list[tuple[str, dict]]:
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
            metadata_url = Url.build_metadata_url(dt_str, instrument)

            try:
                response = requests.get(metadata_url, timeout=15)
                response.raise_for_status()
                last_modified_map = self._fetch_last_modified_map(instrument, dt_str)
                results.append((response.text, last_modified_map))
            except Exception:
                pass

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
    
    def _parse_metadata(self, raw_text: str, last_modified_map: dict[str, str]) -> List[FileMetadata]:
        """
        Parse metadata text into domain objects.

        :param raw_text: Raw metadata content
        :param last_modified_map: filenames and their last modified datetime.
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
                last_modified_utc = last_modified_map.get(filename)
                if not last_modified_utc:
                    continue
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
                        last_modified_utc=last_modified_utc,
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
    
    def _fetch_last_modified_map(self, instrument: Instrument, dt: str) -> dict[str, str]:
        """
        Fetch directory listing and return:
        filename -> last_modified_utc
        """

        url = Url.build_base_path(dt, instrument)

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            html = response.text
        except Exception:
            return {}

        pattern = re.compile(
            r'<a href="([^"]+\.fts)">.*?</a></td><td align="right">(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})',
            re.IGNORECASE
        )

        et = ZoneInfo("America/New_York")
        utc = ZoneInfo("UTC")

        result = {}

        for match in pattern.finditer(html):
            filename = match.group(1)
            date_part = match.group(2)
            time_part = match.group(3)

            try:
                dt_et = datetime.strptime(
                    f"{date_part} {time_part}", "%Y-%m-%d %H:%M"
                ).replace(tzinfo=et)

                result[filename] = dt_et.astimezone(utc).isoformat()

            except Exception:
                continue

        return result