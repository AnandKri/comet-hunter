from pathlib import Path
from datetime import datetime, timedelta, UTC
from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.database.infrastructure.query_executor import QueryExecutor
from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.services.metadata_service import MetadataService
from backend.services.download_file_service import DownloadFileService
from backend.services.slot_service import SlotService
from backend.database.domain.processed_file import ProcessedFile
from backend.util.enums import Instrument
import pytest

pytestmark = pytest.mark.integration


def test_download_service():
    bootstrap_database()

    executor = QueryExecutor()

    processed_repo = ProcessedFileRepository(executor)
    metadata_repo = FileMetadataRepository(executor)
    slot_repo = DownlinkSlotRepository(executor)

    metadata_service = MetadataService(metadata_repo)
    slot_service = SlotService(slot_repo)

    download_dir = Path("./data/raw")
    download_dir.mkdir(parents=True, exist_ok=True)

    download_service = DownloadFileService(
        processed_repository=processed_repo,
        metadata_service=metadata_service,
        download_directory=download_dir,
        max_workers=4
    )

    now = datetime.now(UTC)
    observation_start = (now - timedelta(hours=8)).isoformat()
    observation_end = now.isoformat()
    
    last_slot = slot_service.get_past_slots(
        downlink_start_utc=(now-timedelta(hours=24)).isoformat(),
        downlink_end_utc=now.isoformat()
        )[-1]

    inserted = metadata_service.sync_metadata(
        Instrument.C3,
        downlink_start_utc=last_slot.bot_utc,
        downlink_end_utc=last_slot.eot_utc
    )

    assert isinstance(inserted, int)
    assert inserted >= 0
    downloaded = download_service.download_files_by_observation(
        Instrument.C3,
        observation_start,
        observation_end
    )

    assert isinstance(downloaded, int)
    assert downloaded >= 0
    
    files = download_service.get_downloaded_files_by_time(
        Instrument.C3,
        download_start_utc=observation_end,
        download_end_utc=datetime.now(UTC).isoformat()
    )
    
    assert isinstance(files, list)

    for file in files:
        if file.raw_file_path:
            assert Path(file.raw_file_path).exists()
        assert isinstance(file, ProcessedFile)
    
    if downloaded > 0:
        assert len(files) > 0