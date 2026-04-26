from pathlib import Path
from datetime import datetime, timedelta, UTC

from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.database.infrastructure.query_executor import QueryExecutor

from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository

from backend.services.metadata_service import MetadataService
from backend.services.download_file_service import DownloadFileService
from backend.services.process_file_service import ProcessFileService
from backend.services.slot_service import SlotService

from backend.database.domain.processed_file import ProcessedFile
from backend.util.enums import Instrument, FileStatus

import pytest

pytestmark = pytest.mark.integration


def test_process_file_service():
    bootstrap_database()

    executor = QueryExecutor()

    processed_repo = ProcessedFileRepository(executor)
    metadata_repo = FileMetadataRepository(executor)
    slot_repo = DownlinkSlotRepository(executor)

    metadata_service = MetadataService(metadata_repo)
    slot_service = SlotService(slot_repo)

    raw_dir = Path("./data/raw")
    processed_dir = Path("./data/processed")

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    download_service = DownloadFileService(
        processed_repository=processed_repo,
        metadata_service=metadata_service,
        download_directory=raw_dir,
        max_workers=4
    )

    process_service = ProcessFileService(
        processed_repository=processed_repo,
        metadata_service=metadata_service,
        processed_directory=processed_dir,
        max_workers=4
    )

    now = datetime.now(UTC)
    observation_start = (now - timedelta(hours=8)).isoformat()
    observation_end = now.isoformat()

    last_slot = slot_service.get_past_slots(
        downlink_start_utc=(now-timedelta(hours=24)).isoformat(),
        downlink_end_utc=now.isoformat()
        )[-1]
    
    metadata_service.sync_metadata(
        Instrument.C3,
        last_slot.bot_utc,
        last_slot.eot_utc
    )

    download_service.download_files_by_observation(
        Instrument.C3,
        observation_start_utc=observation_start,
        observation_end_utc=observation_end
    )

    files = download_service.get_downloaded_files_by_time(
        Instrument.C3,
        download_start_utc=observation_start,
        download_end_utc=datetime.now(UTC).isoformat()
    )

    ready_count = process_service.mark_ready_files_for_processing(
        instrument=Instrument.C3,
        observation_start_utc=observation_start,
        observation_end_utc=observation_end
    )

    assert isinstance(ready_count, int)
    assert ready_count >= 0

    processed = process_service.process_pending_files(
        instrument=Instrument.C3,
        observation_start_utc=observation_start,
        observation_end_utc=observation_end
    )

    assert isinstance(processed, int)
    assert processed > 0

    processed_files = processed_repo.get_files_by_observation_and_status(
        Instrument.C3,
        status=FileStatus.PROCESSED,
        observation_start_utc=observation_start,
        observation_end_utc=observation_end
    )

    assert len(processed_files) > 0

    for file in processed_files:
        assert isinstance(file, ProcessedFile)
        if file.processed_file_path:
            assert Path(file.processed_file_path).exists()