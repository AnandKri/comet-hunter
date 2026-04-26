from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.database.infrastructure.query_executor import QueryExecutor
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.services.metadata_service import MetadataService
from backend.services.slot_service import SlotService
from backend.database.domain.file_metadata import FileMetadata
from backend.util.enums import Instrument
from datetime import datetime, timedelta, UTC
import pytest

pytestmark = pytest.mark.integration


def test_metadata_service():
    bootstrap_database()

    executor = QueryExecutor()
    metadata_repo = FileMetadataRepository(executor)
    slot_repo = DownlinkSlotRepository(executor)
    metadata_service = MetadataService(metadata_repo)
    slot_service = SlotService(slot_repo)

    now = datetime.now(UTC)
    observation_start = (now - timedelta(hours=8)).isoformat()
    observation_end = now.isoformat()

    last_slot = slot_service.get_past_slots(
        downlink_start_utc=(now-timedelta(hours=24)).isoformat(),
        downlink_end_utc=now.isoformat()
        )[-1]

    inserted = metadata_service.sync_metadata(
        instrument=Instrument.C3,
        downlink_start_utc=last_slot.bot_utc,
        downlink_end_utc=last_slot.eot_utc
    )

    assert isinstance(inserted, int)
    assert inserted >= 0
    data_downlink = metadata_service.get_metadata_by_downlink(
        Instrument.C3,
        last_slot.bot_utc,
        last_slot.eot_utc
    )

    assert isinstance(data_downlink, list)

    for item in data_downlink:
        assert isinstance(item, FileMetadata)

    data_obs = metadata_service.get_metadata_by_observation(
        Instrument.C3,
        observation_start,
        observation_end
    )
    assert isinstance(data_obs, list)

    for item in data_obs:
        assert isinstance(item, FileMetadata)
    
    for item in data_downlink:
        assert item.instrument == Instrument.C3

    for item in data_obs:
        assert item.instrument == Instrument.C3