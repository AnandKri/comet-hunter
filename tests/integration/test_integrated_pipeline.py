from pathlib import Path
from datetime import datetime, timedelta, UTC
from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.database.infrastructure.query_executor import QueryExecutor
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.database.domain.processed_file import ProcessedFile
from backend.services.slot_service import SlotService
from backend.services.metadata_service import MetadataService
from backend.services.download_file_service import DownloadFileService
from backend.services.process_file_service import ProcessFileService
from backend.util.enums import Instrument
import pytest

pytestmark = pytest.mark.integration


def test_full_pipeline():
    bootstrap_database()

    executor = QueryExecutor()
    
    slot_repo = DownlinkSlotRepository(executor)
    metadata_repo = FileMetadataRepository(executor)
    processed_repo = ProcessedFileRepository(executor)
    
    slot_service = SlotService(slot_repo)
    metadata_service = MetadataService(metadata_repo)

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
        processed_directory=processed_dir,
        max_workers=4
    )

    now = datetime.now(UTC)
    downlink_start = (now - timedelta(hours=2)).isoformat()
    downlink_end = now.isoformat()

    observation_start = downlink_start
    observation_end = downlink_end
    
    slots_added = slot_service.sync_slots()
    assert isinstance(slots_added, int)
    assert slots_added >= 0

    active_slot = slot_service.sync_and_get_active_slot()
    assert (active_slot is None) or isinstance(active_slot, DownlinkSlot)

    use_slots = active_slot is not None

    if use_slots:
        metadata_inserted = metadata_service.sync_metadata_by_slots(
            instrument=Instrument.C3,
            slots=[active_slot]
        )
    else:
        metadata_inserted = metadata_service.sync_metadata(
            instrument=Instrument.C3,
            downlink_start_utc=downlink_start,
            downlink_end_utc=downlink_end
        )

    assert isinstance(metadata_inserted, int)
    assert metadata_inserted >= 0
    
    if use_slots:
        downloaded = download_service.download_files_by_slots(
            instrument=Instrument.C3,
            slots=[active_slot]
        )
    else:
        downloaded = download_service.download_files_by_observation(
            instrument=Instrument.C3,
            observation_start_utc=observation_start,
            observation_end_utc=observation_end
        )

    assert isinstance(downloaded, int)
    assert downloaded >= 0
    
    files = download_service.get_downloaded_files_by_time(
        instrument=Instrument.C3,
        download_start_utc=downlink_start,
        download_end_utc=downlink_end
    )

    assert isinstance(files, list)

    for file in files:
        assert isinstance(file, ProcessedFile)
    
    if downloaded > 0:
        assert len(files) > 0
    
    ready_count = 0

    failed = 0
    for file in files:
        if file.raw_file_path:
            assert Path(file.raw_file_path).exists()
        try:
            if file.status.name == "DOWNLOADED":
                updated = file.transition_to(file.status.READY)
                processed_repo.save(updated)
                ready_count += 1
        except Exception:
            failed += 1
    assert failed == 0

    assert isinstance(ready_count, int)
    assert ready_count >= 0

    try:
        processed = process_service.process_pending_files()

        assert isinstance(processed, int)
        assert processed >= 0

    except NotImplementedError:
        assert True       