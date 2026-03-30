from typing import List, Optional
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.util.constants import Url
from backend.util.enums import SlotStatus

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
        inserted = 0

        for slot in slots:
            if not self._slot_repository.exists(slot.identity()):
                if self._slot_repository.create(slot):
                    inserted += 1
        
        return inserted
    
    def _fetch_slot_data(self) -> str:
        """
        Fetch raw slot page content.

        :return: raw HTML/text content
        """

        # implement requests.get
        raise NotImplementedError
    
    def _parse_slots(self, raw_data: str) -> List[DownlinkSlot]:
        """
        Parse slot data into domain entities.
        
        :param raw_data: raw slot data to be parsed. 
        :return: List of DownlinkSlot entities. Parsed slots
        """

        # implement parser
        raise NotImplementedError
    
    def mark_slot_done(self, slot: DownlinkSlot) -> bool:
        """
        Mark slot as completed.

        :param slot: slot domain entity
        :return: True if updated successfully. False otherwise.
        """

        return self._slot_repository.update_status(SlotStatus.DONE ,slot)
    
    def get_active_slots(self) -> Optional[DownlinkSlot]:
        """
        Fetch active slot if available.
        
        :return: returns DownlinkSlot domain entity of active slot if present
        """

        return self._slot_repository.get_current_active_slot()