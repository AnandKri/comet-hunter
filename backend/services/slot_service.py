from typing import List, Optional
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.util.constants import Url
from backend.util.enums import SlotStatus
from backend.util.funcs import validate_time_window
import requests
import re
from datetime import datetime, timedelta, UTC 

class SlotService:
    """
    Service responsible for:
    - Fetching slot data from remote source
    - Parsing slot information
    - Persisting slots into database
    - Handling slot state updates
    """

    def __init__(self, slot_repository: DownlinkSlotRepository):
        self._slot_repository = slot_repository
    
    def sync_slots(self) -> int:
        """
        Fetch slot data from remote source and update 
        database.

        :return: number of new slots inserted
        """

        raw_data = self._fetch_slot_data()
        slots = self._parse_slots(raw_data)
        if not slots:
            raise RuntimeError("No slots parsed - parser likely broken")
        
        inserted = 0

        for slot in slots:
            if not self._slot_repository.exists(identity=slot.identity()):
                if self._slot_repository.create_slot(slot):
                    inserted += 1
        
        return inserted
    
    def _fetch_slot_data(self) -> str:
        """
        Fetch raw slot page content.

        :return: raw HTML/text content
        """
        try:
            response = requests.get(Url.SCHEDULE, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch slot data: {e}")
    
    def _parse_slots(self, raw_data: str) -> List[DownlinkSlot]:
        """
        Parse slot data into domain entities.
        
        :param raw_data: raw slot data to be parsed. 
        :return: List of DownlinkSlot entities. Parsed slots
        """

        slots: List[DownlinkSlot] = []

        pattern = re.compile(
            r"(\d+)\s+"
            r"(\d+)\s+"
            r"(\w+)\s+"
            r"(\d{4}-\d{2}-\d{2})\s+"
            r"(\d{2}:\d{2})\s*-\s*"
            r"(\d{2}:\d{2})\s+"
            r"([A-Z0-9\-]+)"
        )

        for match in pattern.finditer(raw_data):

            try:
                wk = int(match.group(1))
                doy = int(match.group(2))
                wdy = match.group(3)

                date = match.group(4)
                bot = match.group(5)
                eot = match.group(6)

                ant = match.group(7)

                bot_dt = datetime.fromisoformat(f"{date}T{bot}:00")
                eot_dt = datetime.fromisoformat(f"{date}T{eot}:00")

                if eot_dt < bot_dt:
                    eot_dt += timedelta(days=1)

                bot_utc = bot_dt.replace(tzinfo=UTC).isoformat()
                eot_utc = eot_dt.replace(tzinfo=UTC).isoformat()

                slot = DownlinkSlot(
                    wk=wk,
                    doy=doy,
                    wdy=wdy,
                    bot_utc=bot_utc,
                    eot_utc=eot_utc,
                    ant=ant,
                    status=SlotStatus.PENDING
                )

                slots.append(slot)

            except Exception as e:
                continue # log later

        
        return slots
    
    def mark_slot_done(self, slot: DownlinkSlot) -> Optional[DownlinkSlot]:
        """
        Mark slot as completed.

        :param slot: slot domain entity
        :return: updated slot domain entity (if successful).
        """

        return self._slot_repository.update_status(SlotStatus.DONE ,slot)
    
    def get_active_slot(self) -> Optional[DownlinkSlot]:
        """
        Fetch active slot if available.
        
        :return: returns DownlinkSlot domain entity of active slot if present
        """

        return self._slot_repository.get_active_slot()
    
    def sync_and_get_active_slot(self) -> Optional[DownlinkSlot]:
        """
        Performs slot lifecycle synchronization and optionally returns 
        active slot if any.

        Steps:
        1. Marks expired PENDING slots as MISSED
        2. Returns existing ACTIVE slot if present
        3. Otherwise claims next eligible PENDING slot as ACTIVE

        This method is intended to be called during system initialization
        or scheduling cycles.

        :return: Active DownlinkSlot if available, else None
        """

        now = datetime.now(UTC).isoformat()

        self._slot_repository.mark_expired_active_as_missed(now)
        self._slot_repository.mark_expired_pending_as_missed(now)

        active = self._slot_repository.get_active_slot()
        if active:
            return active

        slot = self._slot_repository.get_next_claimable_slot(now)
        if not slot:
            return None

        slot = self._slot_repository.update_status(SlotStatus.ACTIVE, slot)

        return slot
    
    def delete_completed_slots(self) -> int:
        """
        Deletes completed (`DONE`) slots.

        :return: Number of rows deleted.
        """
        
        return self._slot_repository.delete_completed_slots()
    
    def get_past_slots(self, downlink_start_utc: str, downlink_end_utc: str) -> list[DownlinkSlot]:
        """
        get slots whose time window falls within the time period 
        between start and end.

        :param downlink_start_utc: lower bound timestamp
        :param downlink_end_utc: upper bound timestamp (expected to be current timestamp)
        :return: List of DownlinkSlot domain entities ordered by `bot_utc` 
        """
        validate_time_window(downlink_start_utc, downlink_end_utc)

        return self._slot_repository.get_past_slots(downlink_start_utc=downlink_start_utc, downlink_end_utc=downlink_end_utc)
    
    def get_future_slots(self, downlink_start_utc: str, downlink_end_utc: str) -> list[DownlinkSlot]:
        """
        Returns future slots - which are not yet started.
        
        Could be utilized when there's no current `ACTIVE` slot,
        and we want to see next upcoming slots.

        :param downlink_start_utc: starting timestamp (ISO UTC) (expected to be current timestamp)
        :param downlink_end_utc: Upper bound timestamp (ISO UTC)
        :return: Return list of slot domain entities.
        """

        validate_time_window(downlink_start_utc, downlink_end_utc)

        return self._slot_repository.get_future_slots(downlink_start_utc, downlink_end_utc)
    
    def next_active_slot_in(self) -> Optional[timedelta]:
        """
        Returns the time remaining until the start of next slot.
        This is independent of if currently there exists an `ACTIVE`
        slot or not. 

        Logic:
        - find the earliest `PENDING` slot whose start time is in the future
        - return the time difference between now and its start time.
        """

        now = datetime.now(UTC)

        next_active_slot = self._slot_repository.get_next_active_slot(now.isoformat())
        if not next_active_slot:
            return None
        
        bot_utc = datetime.fromisoformat(next_active_slot.bot_utc)
        return bot_utc - now