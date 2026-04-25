from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.database.infrastructure.query_executor import QueryExecutor
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.services.metadata_service import MetadataService
from backend.database.domain.file_metadata import FileMetadata
from backend.util.enums import Instrument
from datetime import datetime, timedelta, UTC
import pytest

pytestmark = pytest.mark.integration


def test_metadata_service():
    bootstrap_database()

    executor = QueryExecutor()
    metadata_repo = FileMetadataRepository(executor)
    metadata_service = MetadataService(metadata_repo)

    now = datetime.now(UTC)
    start = (now - timedelta(hours=2)).isoformat()
    end = now.isoformat()

    inserted = metadata_service.sync_metadata(
        instrument=Instrument.C3,
        downlink_start_utc=start,
        downlink_end_utc=end
    )
    assert isinstance(inserted, int)
    assert inserted >= 0
    data_downlink = metadata_service.get_metadata_by_downlink(
        Instrument.C3,
        start,
        end
    )
    assert isinstance(data_downlink, list)

    for item in data_downlink:
        assert isinstance(item, FileMetadata)

    data_obs = metadata_service.get_metadata_by_observation(
        Instrument.C3,
        start,
        end
    )
    assert isinstance(data_obs, list)

    for item in data_obs:
        assert isinstance(item, FileMetadata)
    
    for item in data_downlink:
        assert item.instrument == Instrument.C3

    for item in data_obs:
        assert item.instrument == Instrument.C3