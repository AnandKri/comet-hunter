from backend.util.constants import DB
from backend.util.enums import FileStatus, FetchType, OperationType, Instrument
from typing import Optional, ClassVar
from backend.database.domain.processed_file import ProcessedFile
from backend.database.infrastructure.query_spec import QuerySpec
from backend.database.infrastructure.query_executor import QueryExecutor

class ProcessedFileRepository:
    """
    This class is for `processed_file` table required to keep a log
    of which files are processed and which are not. 
    """
    
    table_name: ClassVar[str] = DB.PROCESSED_FILE
    max_processing_attempts: ClassVar[int] = 2
    max_downloading_attempts: ClassVar[int] = 2

    def __init__(self, executor: QueryExecutor):
        self._executor = executor

    @classmethod
    def create_table_sql(cls) -> str:
        """
        Query to create `processed_file` table.
        """

        allowed_statuses = ",".join(f"'{status.value}'" for status in FileStatus)

        return f"""
            CREATE TABLE IF NOT EXISTS {cls.table_name} (
                raw_file_name TEXT PRIMARY KEY,
                raw_file_hash TEXT UNIQUE,
                raw_file_path TEXT UNIQUE NOT NULL,
                raw_file_size INTEGER,
                processed_file_name TEXT UNIQUE,
                processed_file_hash TEXT UNIQUE,
                processed_file_path TEXT UNIQUE,
                processed_file_size INTEGER,
                datetime_of_observation TEXT NOT NULL,
                instrument TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ({allowed_statuses})),
                error_message TEXT,
                downloaded_at TEXT,
                last_downloading_attempt_at TEXT,
                downloading_attempt_count INTEGER NOT NULL DEFAULT 0,
                processed_at TEXT,
                last_processing_attempt_at TEXT,
                processing_attempt_count INTEGER NOT NULL DEFAULT 0
            )
        """
    
    @classmethod
    def create_indexes_sql(cls) -> str:
        """
        Query to create index for `processed_file` table
        for faster accessibility while filtering based 
        on status and datetime_of_observation.
        """
        return f"""
            CREATE INDEX IF NOT EXISTS idx_processed_status_time
            ON {cls.table_name} (status, datetime_of_observation)
        """
    
    def create_file(self,
                    raw_file_name: str,
                    raw_file_hash: Optional[str],
                    raw_file_path: str,
                    raw_file_size: Optional[int],
                    processed_file_name: Optional[str],
                    processed_file_hash: Optional[str],
                    processed_file_path: Optional[str],
                    processed_file_size: Optional[int],
                    datetime_of_observation: str,
                    instrument: Instrument,
                    status: FileStatus,
                    error_message: Optional[str],
                    downloaded_at: Optional[str],
                    last_downloading_attempt_at: Optional[str],
                    downloading_attempt_count: int,
                    processed_at: Optional[str],
                    last_processing_attempt_at: Optional[str],
                    processing_attempt_count: int) -> bool:
        """
        Checks if file status is valid or not.
        creates the file details to a row in the table
        
        :param raw_file_name: raw file name, as appears in img-hdr.txt - primary key
        :param raw_file_hash: hash value of unprocessed file
        :param raw_file_path: raw file path.
        :param raw_file_size: raw file size in bytes.
        :param processed_file_name: renamed processed file.
        :param processed_file_hash: hash value of processed file.
        :param processed_file_path: processed file path.
        :param processed_file_size: processed file size in bytes
        :param datetime_of_observation: date time of observation
        :param instrument: instrument used for observation
        :param status: file processing status
        :param error_message: error thrown as a result of failed file processing 
        :param downloaded_at: UTC timestamp when file downloaded.
        :param last_downloading_attempt_at: UTC timestamp of the most recent downloading attempt.
        :param downloading_attempt_count: Number of downloading attempts made.
        :param processed_at: UTC timestamp when processing completed.
        :param last_processing_attempt_at: UTC timestamp of the most recent processing attempt.
        :param processing_attempt_count: Number of processing attempts made.
        :return: Returns True only if the number of created rows is 1
        """
        
        if not isinstance(status, FileStatus):
            raise ValueError("status must be FileStatus enum")
        if not isinstance(instrument, Instrument):
            raise ValueError("instrument should be Instrument enum")
        
        spec = QuerySpec(
            sql = f"""
                INSERT OR IGNORE INTO {self.table_name}
                (raw_file_name,
                raw_file_hash,
                raw_file_path,
                raw_file_size,
                processed_file_name,
                processed_file_hash,
                processed_file_path,
                processed_file_size,
                datetime_of_observation,
                instrument,
                status,
                error_message,
                downloaded_at,
                last_downloading_attempt_at,
                downloading_attempt_count,
                processed_at,
                last_processing_attempt_at,
                processing_attempt_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            operation=OperationType.WRITE,
            params=(
                    raw_file_name,
                    raw_file_hash,
                    raw_file_path,
                    raw_file_size,
                    processed_file_name,
                    processed_file_hash,
                    processed_file_path,
                    processed_file_size,
                    datetime_of_observation,
                    instrument.value,
                    status.value,
                    error_message,
                    downloaded_at,
                    last_downloading_attempt_at,
                    downloading_attempt_count,
                    processed_at,
                    last_processing_attempt_at,
                    processing_attempt_count
                )
        )
        
        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def read_file_by_name(self, raw_file_name: str) -> Optional[ProcessedFile]:
        """
        Fetch processed file record using raw file name value

        :param raw_file_name: Computed name value of raw file, primary key
        :return : returns complete file processing data
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

        return ProcessedFile.from_row(result.data)

    def delete_file(self, file: ProcessedFile) -> bool:
        """
        Deletes processed file record

        :param file: processed file domain entity
        :return : Returns boolean value, True if deletion happened
        """

        spec = QuerySpec(
            sql=f"""
                DELETE FROM {self.table_name}
                WHERE raw_file_name = ?
            """,
            operation=OperationType.WRITE,
            params=(file.raw_file_name,)
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def save(self, file: ProcessedFile) -> bool:
        """
        Persists latest state of a processed file domain entity.

        :param file: Domain object containing latest state.
        :return: True if exactly one row updated.
        """

        spec = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET status = ?,
                    error_message = ?,
                    downloaded_at = ?,
                    last_downloading_attempt_at = ?,
                    downloading_attempt_count = ?,
                    processed_file_hash = ?,
                    processed_file_name = ?,
                    processed_file_path = ?,
                    processed_file_size = ?,
                    processed_at = ?,
                    last_processing_attempt_at = ?,
                    processing_attempt_count = ?
                WHERE raw_file_name = ?
            """,
            operation=OperationType.WRITE,
            params=(
                file.status.value,
                file.error_message,
                file.downloaded_at,
                file.last_downloading_attempt_at,
                file.downloading_attempt_count,
                file.processed_file_hash,
                file.processed_file_name,
                file.processed_file_path,
                file.processed_file_size,
                file.processed_at,
                file.last_processing_attempt_at,
                file.processing_attempt_count,
                file.raw_file_name
            )
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1

    def exists_by_name(self, raw_file_name: str) -> bool:
        """
        Checks if a processed file record exists.

        :param raw_file_name: Raw file name.
        :return: True if record exists.
        """

        spec = QuerySpec(
            sql=f"""
                SELECT 1
                FROM {self.table_name}
                WHERE raw_file_name = ?
            """,
            operation=OperationType.READ,
            params=(raw_file_name,),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        return result.data is not None

    def claim_next_ready(self) -> Optional[ProcessedFile]:
        """
        Claims next READY file for processing.
        :return: Next file to process or None.
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE status = ?
                ORDER BY last_processing_attempt_at ASC
                LIMIT 1
            """,
            operation=OperationType.READ,
            params=(FileStatus.READY.value,),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        if not result.data:
            return None

        return ProcessedFile.from_row(result.data)

    def get_retryable_process(self) -> list[ProcessedFile]:
        """
        Fetch files eligible for processing retry.

        :return: Retryable files.
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE status = ?
                AND processing_attempt_count < ?
                ORDER BY last_processing_attempt_at ASC
            """,
            operation=OperationType.READ,
            params=(
                FileStatus.PROCESSING_FAILED.value,
                self.max_processing_attempts
            ),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if not result.data:
            return []

        return [
            ProcessedFile.from_row(row)
            for row in result.data
        ]
    
    def get_retryable_download(self) -> list[ProcessedFile]:
        """
        Fetch files eligible for download retry.

        :return: Retryable files.
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE status = ?
                AND downloading_attempt_count < ?
                ORDER BY last_downloading_attempt_at ASC
            """,
            operation=OperationType.READ,
            params=(
                FileStatus.DOWNLOADING_FAILED.value,
                self.max_downloading_attempts
            ),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if not result.data:
            return []

        return [
            ProcessedFile.from_row(row)
            for row in result.data
        ]
    
    def get_ready_files(self) -> list[ProcessedFile]:
        """
        Fetch files ready for processing

        :return: list of files in `READY` state
        """

        spec = QuerySpec(
            sql = f"""
                    SELECT *
                    FROM {self.table_name}
                    WHERE status = ?
                    ORDER BY last_processing_attempt_at ASC
                """,
            operation=OperationType.READ,
            params=(FileStatus.READY.value,),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if not result.data:
            return []

        return [ProcessedFile.from_row(r) for r in result.data]
    
    def get_downloaded_files_by_time(self, instrument: Instrument, download_start_utc: str, download_end_utc: str) -> list[ProcessedFile]:
        """
        get downloaded files by instrument and download_at time window
        
        :param instrument: instrument used for observation
        :param download_start_utc: start timestamp (ISO)
        :param download_end_utc: end timestamp (ISO)
        :return: list of process file entities
        """

        spec = QuerySpec(
            sql = f"""
                    SELECT *
                    FROM {self.table_name}
                    WHERE downloaded_at >= ?
                    AND downloaded_at <= ?
                    AND instrument = ?
                    ORDER BY downloaded_at ASC
                """,
            operation=OperationType.READ,
            params=(download_start_utc,
                    download_end_utc,
                    instrument.value),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if not result.data:
            return []

        return [ProcessedFile.from_row(r) for r in result.data]