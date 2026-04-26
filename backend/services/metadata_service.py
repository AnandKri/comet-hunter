from typing import List, Optional
import requests
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.domain.file_metadata import FileMetadata
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.services.slot_service import SlotService
from backend.util.constants import Url
from backend.util.enums import Instrument
from backend.util.funcs import validate_time_window
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
    
    def sync_metadata(self, instrument: Instrument, downlink_start_utc: Optional[str] = None, downlink_end_utc: Optional[str] = None) -> int:
        """
        Fetch metadata from remote source and update database.

        If `downlink_start_utc` is not provided, it is inferred from DB (latest available record).
        If `downlink_end_utc` is not provided, current UTC time is used.

        :param instrument: instrument to sync (C2/C3)
        :param downlink_start_utc: start datetime (ISO string, optional)
        :param downlink_end_utc: end datetime (ISO string, optional)
        :return: number of new records inserted
        """

        validate_time_window(downlink_start_utc, downlink_end_utc)

        if downlink_end_utc is None:
            downlink_end_utc = datetime.now(UTC).isoformat()
        if downlink_start_utc is None:
            downlink_start_utc = self._metadata_repository.get_latest_last_modified(instrument)
            if downlink_start_utc is None:
                downlink_start_utc = (datetime.fromisoformat(downlink_end_utc) - timedelta(days=1)).isoformat()
            else:
                downlink_start_utc = (datetime.fromisoformat(downlink_start_utc) - timedelta(days=1)).isoformat()

        all_metadata = []

        downlink_start_dt_utc = datetime.fromisoformat(downlink_start_utc)
        downlink_end_dt_utc = datetime.fromisoformat(downlink_end_utc)

        for raw_text, last_modified_map in self._fetch_metadata(instrument, downlink_start_utc, downlink_end_utc):
            parsed = self._parse_metadata(raw_text, last_modified_map)
            filtered = [f for f in parsed
                        if downlink_start_dt_utc <= datetime.fromisoformat(f.last_modified_utc) <= downlink_end_dt_utc
                        ]
            all_metadata.extend(filtered)
        
        new_files = self._discover_new_files(all_metadata)

        return self._metadata_repository.bulk_create_metadata(new_files)
    
    def _fetch_metadata(self, instrument: Instrument, downlink_start_utc: str, downlink_end_utc: str) -> list[tuple[str, dict]]:
        """
        Fetch metadata for each day in a given range.

        :param instrument: instrument (C2/C3)
        :param downlink_start_utc: start datetime (ISO string)
        :param downlink_end_utc: end datetime (ISO string), supposed to be current datetime
        :return: list of raw metadata text (one per day)
        """

        downlink_start_date_utc = datetime.fromisoformat(downlink_start_utc).date()
        downlink_end_date_utc = datetime.fromisoformat(downlink_end_utc).date()
        downlink_current_utc = downlink_start_date_utc

        results = []

        while downlink_current_utc <= downlink_end_date_utc:
            downlink_dt_str_utc = downlink_current_utc.isoformat()
            metadata_url = Url.build_metadata_url(downlink_dt_str_utc, instrument)

            try:
                response = requests.get(metadata_url, timeout=15)
                response.raise_for_status()
                last_modified_map = self._fetch_last_modified_map(instrument, downlink_dt_str_utc)
                results.append((response.text, last_modified_map))
            except Exception:
                pass

            downlink_current_utc += timedelta(days=1)
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
    
    def _fetch_last_modified_map(self, instrument: Instrument, downlink_dt_utc: str) -> dict[str, str]:
        """
        Fetch directory listing and return:
        filename -> last_modified_utc
        """

        url = Url.build_base_path(downlink_dt_utc, instrument)

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
    
    def get_metadata_by_slots(self, instrument: Instrument, slots: list[DownlinkSlot]) -> list[FileMetadata]:
        """
        returns files metadata entities for a given slot and instrument

        :param instrument: instrument used for observation
        :param slots: list of slots domain entities
        :return: list of file metadata entities
        """

        if not slots:
            return []
        
        downlink_start_utc = min(slot.bot_utc for slot in slots)
        downlink_end_utc = max(slot.eot_utc for slot in slots)
        
        return self._metadata_repository.get_metadata_by_slot(
            instrument=instrument,
            downlink_start_utc=downlink_start_utc,
            downlink_end_utc=downlink_end_utc
        )
    
    def get_metadata_by_downlink(self, instrument: Instrument, downlink_start_utc: str, downlink_end_utc: str) -> List[FileMetadata]:
        """
        returns file metadata for a given time window and instrument

        :param instrument: instrument used for observation
        :param downlink_start_utc: start timestamp (ISO)
        :param downlink_end_utc: end timestamp (ISO)
        :return: list of file metadata domain entities
        """

        validate_time_window(downlink_start_utc, downlink_end_utc)
        
        return self._metadata_repository.get_metadata_by_slot(
            instrument, 
            downlink_start_utc, 
            downlink_end_utc
        )
    
    def get_metadata_by_active_slot(self, instrument: Instrument, slot_service: SlotService) -> list[FileMetadata]:
        """
        Fetch metadata for current active slot.

        :param instrument: instrument used for observation
        :param slot_service: slot service instance
        :return: list of metadata files domain entities
        """

        slot = [slot_service.sync_and_get_active_slot()]

        if not slot:
            return []
        
        return self.get_metadata_by_slots(slot, instrument)
    
    def sync_metadata_by_slots(self, instrument: Instrument, slots: list[DownlinkSlot]) -> int:
        """
        Sync metadata for given slots. takes start date of earliest slot and end date of latest slot. 

        :param instrument: instrument used for observation
        :param slots: list of slots domain entities
        :return: number of files metadata inserted into db
        """

        if not slots:
            return 0
        
        downlink_start_utc = min(slot.bot_utc for slot in slots)
        downlink_end_utc = max(slot.eot_utc for slot in slots)

        return self.sync_metadata(instrument, downlink_start_utc, downlink_end_utc)
    
    def get_metadata_by_observation(self, instrument: Instrument, observation_start_utc: str, observation_end_utc: str) -> list[FileMetadata]:
        """
        get metadata for the instrument and observation time window

        :param instrument: instrument used for observation
        :param observation_start_utc: start observation timestamp (ISO) 
        :param observation_end_utc: end observation timestamp (ISO)
        :return: list of file metadata domain entities 
        """
        validate_time_window(observation_start_utc, observation_end_utc)

        return self._metadata_repository.get_metadata_by_observation(
            instrument,
            observation_start_utc,
            observation_end_utc
        )
    
    def read_metadata(self, raw_file_name: str) -> Optional[FileMetadata]:
        """
        Fetch metadata using raw file name

        :param raw_file_name: raw file name primary key
        :return: returns complete file metadata 
        """

        return self._metadata_repository.read_metadata(raw_file_name)