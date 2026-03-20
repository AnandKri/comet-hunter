from backend.util.constants import DB
from backend.util.enums import FetchType, OperationType
from typing import Optional, ClassVar
from backend.database.infrastructure.base import DatabaseBase
from backend.database.domain.file_metadata import FileMetadata
from backend.database.infrastructure.query_spec import QuerySpec
from backend.database.infrastructure.query_executor import QueryExecutor

class FileMetadataRepository:
    """
    This class is for `file_metadata` table required to keep a log
    of file metadata, useful beforehand while retrieving the raw data.
    """
    
    table_name: ClassVar[str] = DB.FILE_METADATA

    def __init__(self, executor: QueryExecutor):
        self._executor = executor

    @classmethod
    def create_table_sql(cls) -> str:
        """
        Query to create `file_metadata` table.
        """
        return f"""
            CREATE TABLE IF NOT EXISTS {cls.table_name} (
                raw_file_name TEXT PRIMARY KEY,
                raw_file_hash TEXT,
                datetime_of_observation TEXT NOT NULL,
                instrument TEXT NOT NULL,
                exposure_time REAL NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                roll REAL NOT NULL
            )
        """
    
    @classmethod
    def create_indexes_sql(cls) -> str:
        """
        Query to create index for `file_metadata` table
        for faster accessbility.
        """
        return f"""
            CREATE INDEX IF NOT EXISTS idx_file_metadata_time
            ON {cls.table_name} (instrument, datetime_of_observation)

            CREATE INDEX IF NOT EXISTS idx_file_metadata_hash
            ON {cls.table_name} (raw_file_hash)
        """
    
    def create_metadata(self, 
                        raw_file_name: str, 
                        raw_file_hash: Optional[str],
                        datetime_of_observation: str,
                        instrument: str, 
                        exposure_time: float, 
                        width: int, 
                        height: int, 
                        roll: float) -> bool:
        """
        creates the file metadata to a row in the table

        :param raw_file_name: raw file name, acts as primary key
        :param raw_file_hash: hash value of unprocessed file 
        :param datetime_of_observation: date of observation
        :param instrument: instrument used to capture the file
        :param exposure_time: exposure time in seconds
        :param width: width in pixels
        :param height: height in pixels
        :param roll: frame roll if any
        :return: Returns True only if the number of created rows is 1
        """
        
        spec = QuerySpec(
            sql = f"""
                INSERT OR IGNORE INTO {self.table_name}
                (raw_file_name,
                raw_file_hash,
                datetime_of_observation,
                instrument, 
                exposure_time, 
                width, 
                height, 
                roll)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
            operation=OperationType.WRITE,
            params=(
                    raw_file_name, 
                    raw_file_hash, 
                    datetime_of_observation,
                    instrument,
                    exposure_time, 
                    width, 
                    height, 
                    roll
                )
        )
        
        result = self._executor.execute(spec)
        
        return result.rows_affected == 1
    
    def read_metadata(self, raw_file_name: str) -> Optional[FileMetadata]:
        """
        Fetch metadata using raw file name

        :param raw_file_name: raw file name primary key
        :return: returns complete file metadata 
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE raw_file_name = ?
            """,
            operation=OperationType.READ,
            params=(raw_file_name,),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        if result.data is None:
            return None
        
        return FileMetadata.from_row(result.data)

    def update_hash(self, file: FileMetadata) -> bool:
        """
        Updates hash value of raw file

        :param file: FileMetadata domain entity containing updated hash
        :return: True only if exactly one row was updated
        """

        spec = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET raw_file_hash = ?
                WHERE raw_file_name = ?
            """,
            operation=OperationType.WRITE,
            params=(
                file.raw_file_hash,
                file.raw_file_name
            )
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1

    def delete_metadata(self, file: FileMetadata) -> bool:
        """
        Deletes metadata entry for a file

        :param file: file domain entity
        :return : returns boolean value, True when deletion happened
        """

        spec=QuerySpec(
            sql=f"""
                DELETE FROM {self.table_name}
                WHERE raw_file_name = ?
            """,
            operation=OperationType.WRITE,
            params=(file.raw_file_name,)
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def exists_by_filename(self, raw_file_name: str) -> bool:
        """
        Checks if metadata entry exists

        :param raw_file_name: raw file name
        :return: True if row exists
        """

        spec = QuerySpec(
            sql=f"""
                SELECT 1
                FROM {self.table_name}
                WHERE raw_file_name = ?
                LIMIT 1
            """,
            operation=OperationType.READ,
            params=(raw_file_name,),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        return result.data is not None
    
    def get_files_for_slot(self, instrument: str, start: str, end: str) -> list[FileMetadata]:
        """
        Fetch metadata for a specific instrument within a time range

        :param instrument: instrument name
        :param start: start datetime (ISO string)
        :param end: end datetime (ISO string)
        :return: list of FileMetadata objects
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE instrument = ?
                AND datetime_of_observation >= ?
                AND datetime_of_observation <= ?
                ORDER BY datetime_of_observation ASC
            """,
            operation=OperationType.READ,
            params=(instrument, start, end),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if not result.data:
            return []

        return [FileMetadata.from_row(row) for row in result.data]
    
    def get_missing_hash_files(self, instrument: str, limit: int) -> list[FileMetadata]:
        """
        Fetch metadata records where raw file hash is not yet populated.

        Useful for identifying files that require hash computation
        after discovery/download

        :param limit: Optional maximum number of records to return
        :return: returns a List of FileMetadata domain objects
        """
        spec = QuerySpec(
            sql = f"""
                SELECT *
                FROM {self.table_name}
                WHERE raw_file_hash IS NULL
                ORDER BY datetime_of_observation ASC
                LIMIT ?
                """,
            operation=OperationType.READ,
            params=(),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if result.data is None:
            return []
        
        return [FileMetadata.from_row(row) for row in result.data]
    
    def exists_by_hash(self, raw_file_hash: str) -> bool:
        """
        Checks if a metadata entry exists for a given raw file hash.

        Useful for idempotency checks and preventing duplicate
        ingestion into downstream processing stages.

        :param raw_file_hash: Hash value of raw file
        :return: returns True if metadata exists
        """
        spec = QuerySpec(
            sql=f"""
                SELECT 1
                FROM {self.table_name}
                WHERE raw_file_hash = ?
                LIMIT 1
                """,
                operation=OperationType.READ,
                params=(raw_file_hash,),
                fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        return result.data is not None
    
    def get_by_hash(self, raw_file_hash: str) -> Optional[FileMetadata]:
        """
        Fetch metadata using raw file hash.

        Useful when processing pipeline operates on hash identity
        and metadata needs to be retrieved without relying on filename.

        :param raw_file_hash: Hash value of raw file
        :return: FileMetadata domain object if found
        """
        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE raw_file_hash = ?
                """,
                operation=OperationType.READ,
                params=(raw_file_hash,),
                fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        if result.data is None:
            return None
        
        return FileMetadata.from_row(result.data)
    
    
    # def bulk_create_metadata(self, files: list[FileMetadata]) -> int:
    # def get_by_names(self, raw_file_names: list[str]) -> list[FileMetadata]:
    # def get_recent_files(self, limit: int, instrument: str) -> list[FileMetadata]: