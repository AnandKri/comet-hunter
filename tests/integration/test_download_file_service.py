from pathlib import Path
from datetime import datetime, timedelta, UTC
from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.database.infrastructure.query_executor import QueryExecutor
from backend.database.repositories.processed_file_repository import ProcessedFileRepository
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.services.metadata_service import MetadataService
from backend.services.download_file_service import DownloadFileService
from backend.database.domain.processed_file import ProcessedFile
from backend.util.enums import Instrument
import pytest

pytestmark = pytest.mark.integration


def test_download_service():
    bootstrap_database()

    executor = QueryExecutor()

    processed_repo = ProcessedFileRepository(executor)
    metadata_repo = FileMetadataRepository(executor)

    metadata_service = MetadataService(metadata_repo)

    download_dir = Path("./data/raw")
    download_dir.mkdir(parents=True, exist_ok=True)

    download_service = DownloadFileService(
        processed_repository=processed_repo,
        metadata_service=metadata_service,
        download_directory=download_dir,
        max_workers=4
    )

    now = datetime.now(UTC)
    start = (now - timedelta(hours=2)).isoformat()
    end = now.isoformat()
    
    inserted = metadata_service.sync_metadata(
        Instrument.C3,
        downlink_start_utc=start,
        downlink_end_utc=end
    )

    assert isinstance(inserted, int)
    assert inserted >= 0
    downloaded = download_service.download_files_by_observation(
        Instrument.C3,
        observation_start_utc=start,
        observation_end_utc=end
    )

    assert isinstance(downloaded, int)
    assert downloaded >= 0
    
    files = download_service.get_downloaded_files_by_time(
        Instrument.C3,
        download_start_utc=start,
        download_end_utc=end
    )
    
    assert isinstance(files, list)

    for file in files:
        if file.raw_file_path:
            assert Path(file.raw_file_path).exists()
        assert isinstance(file, ProcessedFile)
    
    if downloaded > 0:
        assert len(files) > 0