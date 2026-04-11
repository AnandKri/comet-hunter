from backend.database.infrastructure.base import DatabaseBase
from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
from backend.database.repositories.file_metadata_repository import FileMetadataRepository
from backend.database.repositories.processed_file_repository import ProcessedFileRepository

def bootstrap_database():
    DatabaseBase.initialize_database()

    with DatabaseBase.get_connection() as conn:
        conn.execute(DownlinkSlotRepository.create_table_sql())
        conn.execute(DownlinkSlotRepository.create_indexes_sql())
        conn.execute(ProcessedFileRepository.create_table_sql())
        conn.execute(ProcessedFileRepository.create_indexes_sql())
        conn.execute(FileMetadataRepository.create_table_sql())
        for sql in FileMetadataRepository.create_indexes_sql():
            conn.execute(sql)