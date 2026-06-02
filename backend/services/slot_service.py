from typing import List, Optional
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.util.constants import Url
from backend.util.enums import SlotStatus
from backend.util.funcs import validate_time_window
from backend.jobs.exceptions import CancelledError
import requests
import re
from datetime import datetime, timedelta, UTC
from threading import Event
import logging

logger = logging.getLogger(__name__)

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
    
    def sync_slots(self, cancel_event: Event) -> int:
        """
        Fetch slot data from remote source and update 
        database.
        :param cancel_event: event to track cancel request from user.

        :return: number of new slots inserted
        """
        logger.info("Slot sync service execution started")
        try:
            if cancel_event and cancel_event.is_set():
                raise CancelledError()
            raw_data = self._fetch_slot_data()
            if cancel_event and cancel_event.is_set():
                raise CancelledError()
            slots = self._parse_slots(raw_data)
            if not slots:
                raise RuntimeError("No slots parsed - parser likely broken")
            
            inserted = 0

            for slot in slots:
                if cancel_event and cancel_event.is_set():
                    raise CancelledError()
                if not self._slot_repository.exists(identity=slot.identity()):
                    if self._slot_repository.create_slot(slot):
                        inserted += 1
            logger.info(
                "Slot sync service execution completed",
                extra={
                    "slots_parsed": len(slots),
                    "slots_inserted": inserted
                }
            )
            
            return inserted
        except CancelledError:
            logger.info("Slot sync service execution cancelled")
            raise

        except Exception:
            logger.exception("Slot sync service execution failed")
            raise
    
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

                bot_utc = datetime.fromisoformat(f"{date}T{bot}:00").replace(tzinfo=UTC)
                eot_utc = datetime.fromisoformat(f"{date}T{eot}:00").replace(tzinfo=UTC)

                if eot_utc <= bot_utc:
                    eot_utc += timedelta(days=1)
                
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
        Return the current active slot if available.

        Workflow:
        1. Reconcile expired slot states
        2. Return existing ACTIVE slot if present
        3. Claim next eligible PENDING slot if applicable

        :return: Active DownlinkSlot if available, else None
        """

        logger.info("Active slot retrieval started")

        try:
            self.reconcile_slot_states()

            active = self._slot_repository.get_active_slot()

            if active:
                logger.info(
                    "Existing active slot found",
                    extra={
                        "downlink_start_utc": active.bot_utc,
                        "downlink_end_utc": active.eot_utc
                    }
                )
                return active

            logger.info("No existing active slot found")

            now = datetime.now(UTC)

            slot = self._slot_repository.get_next_claimable_slot(now)

            if not slot:
                logger.info("No claimable pending slot found")
                return None

            slot = self._slot_repository.update_status(
                SlotStatus.ACTIVE,
                slot
            )

            logger.info(
                "Pending slot claimed as active",
                extra={
                    "downlink_start_utc": slot.bot_utc,
                    "downlink_end_utc": slot.eot_utc
                }
            )

            return slot

        except Exception:
            logger.exception("Active slot retrieval failed")
            raise
    
    def reconcile_slot_states(self) -> None:
        """
        Reconcile slot lifecycle states based on current UTC time.

        Transitions:
        - ACTIVE -> MISSED
        - PENDING -> MISSED

        :return: None
        """
        logger.info("Slot state reconciliation started")

        try:
            now = datetime.now(UTC)

            self._slot_repository.mark_expired_active_as_missed(now)
            self._slot_repository.mark_expired_pending_as_missed(now)

            logger.info("Slot state reconciliation completed")

        except Exception:
            logger.exception("Slot state reconciliation failed")
            raise

    def delete_completed_slots(self) -> int:
        """
        Deletes completed (`DONE`) slots.

        :return: Number of rows deleted.
        """
        
        return self._slot_repository.delete_completed_slots()
    
    def get_past_slots(self, downlink_start_utc: datetime, downlink_end_utc: datetime) -> list[DownlinkSlot]:
        """
        get slots whose time window falls within the time period 
        between start and end.

        :param downlink_start_utc: lower bound timestamp
        :param downlink_end_utc: upper bound timestamp (expected to be current timestamp)
        :return: List of DownlinkSlot domain entities ordered by `bot_utc` 
        """
        validate_time_window(downlink_start_utc, downlink_end_utc)

        return self._slot_repository.get_past_slots(downlink_start_utc=downlink_start_utc, downlink_end_utc=downlink_end_utc)
    
    def get_future_slots(self, downlink_start_utc: datetime, downlink_end_utc: datetime) -> list[DownlinkSlot]:
        """
        Returns future slots - which are not yet started.
        
        Could be utilized when there's no current `ACTIVE` slot,
        and we want to see next upcoming slots.

        :param downlink_start_utc: starting UTC timestamp (expected to be current timestamp)
        :param downlink_end_utc: Upper bound UTC timestamp
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

        next_active_slot = self._slot_repository.get_next_active_slot(now)
        if not next_active_slot:
            return None
        
        return next_active_slot.bot_utc - now
    
    def get_next_active_slot(self) -> Optional[DownlinkSlot]:
        """
        Returns the next active slot if present. This is intended to be used
        after no active slot is found and next upcoming active slot is required.

        :return: Active DownlinkSlot if available, else None
        """
        now = datetime.now(UTC)

        return self._slot_repository.get_next_active_slot(now)