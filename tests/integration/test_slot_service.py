from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.database.infrastructure.query_executor import QueryExecutor
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.services.slot_service import SlotService
from backend.database.domain.downlink_slot import DownlinkSlot

from datetime import datetime, timedelta, UTC
import pytest

pytestmark = pytest.mark.integration


def test_slot_service():
    bootstrap_database()

    executor = QueryExecutor()
    slot_repo = DownlinkSlotRepository(executor)
    slot_service = SlotService(slot_repo)
    
    inserted = slot_service.sync_slots()
    assert isinstance(inserted, int)
    assert inserted >= 0

    active = slot_service.sync_and_get_active_slot()
    assert (active is None) or isinstance(active, DownlinkSlot)

    now = datetime.now(UTC)
    past_start = (now - timedelta(hours=6)).isoformat()
    future_end = (now + timedelta(hours=6)).isoformat()

    past_slots = slot_service.get_past_slots(past_start, now.isoformat())
    future_slots = slot_service.get_future_slots(now.isoformat(), future_end)

    assert isinstance(past_slots, list)
    assert isinstance(future_slots, list)

    for slot in past_slots:
        assert isinstance(slot, DownlinkSlot)

    for slot in future_slots:
        assert isinstance(slot, DownlinkSlot)