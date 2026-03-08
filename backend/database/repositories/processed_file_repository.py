from backend.util.constants import DB
from backend.util.enums import FileStatus, FetchType, OperationType
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

    def __init__(self, executor: QueryExecutor):
        self._executor = executor

    @classmethod
    def create_table_sql(cls) -> str:
        """
        Query to create `processed_file` table.
        """
        return f"""
            CREATE TABLE IF NOT EXISTS {cls.table_name} (
                raw_file_hash TEXT PRIMARY KEY,
                raw_file_name TEXT UNIQUE NOT NULL,
                raw_file_path TEXT UNIQUE NOT NULL,
                raw_file_size INTEGER NOT NULL,
                processed_file_hash UNIQUE TEXT,
                processed_file_name UNIQUE TEXT,
                processed_file_path UNIQUE TEXT,
                processed_file_size INTEGER,
                status TEXT NOT NULL CHECK(status IN ('{FileStatus.SUCCESS.value}',
                '{FileStatus.FAILED.value}','{FileStatus.PENDING.value}','{FileStatus.NEW.value}')),
                error_message TEXT,
                processed_at TEXT,
                last_attempt_at TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 1
            )
        """
    
    @classmethod
    def create_indexes_sql(cls) -> str:
        """
        Query to create index for `processed_file` table
        for faster accessibility while filtering based 
        on status and last_attempt_at.
        """
        return f"""
            CREATE INDEX IF NOT EXISTS idx_processed_status_time
            ON {cls.table_name} (status, last_attempt_at)
        """
    
    def create_file(self,
                    raw_file_hash: str,
                    raw_file_name: str,
                    raw_file_path: str,
                    raw_file_size: int,
                    processed_file_hash: Optional[str],
                    processed_file_name: Optional[str],
                    processed_file_path: Optional[str],
                    processed_file_size: Optional[int],
                    status: FileStatus,
                    error_message: Optional[str],
                    processed_at: Optional[str],
                    last_attempt_at: str,
                    attempt_count: int) -> bool:
        """
        Checks if file status is valid or not.
        creates the file details to a row in the table
        
        :param raw_file_hash: hash value of unprocessed file, works as primary key
        :param raw_file_name: raw file name, as appears in img-hdr.txt
        :param raw_file_path: raw file path.
        :param raw_file_size: raw file size in bytes.
        :param processed_file_hash: hash value of processed file.
        :param processed_file_name: renamed processed file.
        :param processed_file_path: processed file path.
        :param processed_file_size: processed file size in bytes
        :param status: file processing status
        :param error_message: error thrown as a result of failed file processing 
        :param processed_at: timestamp at which file processing was completed
        :param last_attempt_at: timestamp at which latest processing attempt was made.
        :param attempt_count: number of tries for processing the file
        :return: Returns True only if the number of created rows is 1
        """
        
        if not isinstance(status, FileStatus):
            raise ValueError("status must be FileStatus enum")
        
        spec = QuerySpec(
            sql = f"""
                INSERT OR IGNORE INTO {self.table_name}
                (raw_file_hash,
                raw_file_name,
                raw_file_path,
                raw_file_size,
                processed_file_hash,
                processed_file_name,
                processed_file_path,
                processed_file_size,
                status,
                error_message,
                processed_at,
                last_attempt_at,
                attempt_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            operation=OperationType.WRITE,
            params=(
                    raw_file_hash,
                    raw_file_name,
                    raw_file_path,
                    raw_file_size,
                    processed_file_hash,
                    processed_file_name,
                    processed_file_path,
                    processed_file_size,
                    status.value,
                    error_message,
                    processed_at,
                    last_attempt_at,
                    attempt_count
                )
        )
        
        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def read_file(self, raw_file_hash: str) -> Optional[ProcessedFile]:
        """
        Fetch processed file record

        :param raw_file_hash: Computed hash value of raw file, primary key
        :return : returns complete file processing data
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

        return ProcessedFile.from_row(result.data)
    
    def update_status(self, file: ProcessedFile) -> bool:
        """
        Updates file processing status using the domain object

        :param file: ProcessedFile domain object
        :return: True only if exactly one row was updated
        """

        if not isinstance(file.status, FileStatus):
            raise ValueError("status must be FileStatus enum")

        spec = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET status = ?,
                    error_message = ?,
                    processed_at = ?,
                    last_attempt_at = ?,
                    attempt_count = ?
                WHERE raw_file_hash = ?
            """,
            operation=OperationType.WRITE,
            params=(
                file.status.value,
                file.error_message,
                file.processed_at,
                file.last_attempt_at,
                file.attempt_count,
                file.raw_file_hash
            )
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1

    def delete_file(self, file: ProcessedFile) -> bool:
        """
        Deletes processed file record

        :param file: processed file domain entity
        :return : Returns boolean value, True if deletion happened
        """

        spec = QuerySpec(
            sql=f"""
                DELETE FROM {self.table_name}
                WHERE raw_file_hash = ?
            """,
            operation=OperationType.WRITE,
            params=(file.raw_file_hash,)
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def claim_next_file(self) -> Optional[ProcessedFile]:
        """
        Claims next file for processing.
        Updates last_attempt_at and increments attempt_count.
        """

        spec = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET last_attempt_at = datetime('now'),
                    attempt_count = attempt_count + 1
                WHERE raw_file_hash = (
                    SELECT raw_file_hash
                    FROM {self.table_name}
                    WHERE status IN (?, ?)
                    ORDER BY last_attempt_at ASC
                    LIMIT 1
                )
                RETURNING *
            """,
            operation=OperationType.READ,
            params=(FileStatus.PENDING.value,),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        if result.data is None:
            return None

        return ProcessedFile.from_row(result.data)

    def increment_attempt(self, file: ProcessedFile) -> bool:
        """
        Increment attempt counter and update attempt timestamp.

        :param file: ProcessedFile domain object
        :return : Returns true if successful
        """

        spec = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET attempt_count = attempt_count + 1,
                    last_attempt_at = datetime('now')
                WHERE raw_file_hash = ?
            """,
            operation=OperationType.WRITE,
            params=(file.raw_file_hash,)
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1

    def mark_success(self, file: ProcessedFile) -> bool:
        """
        Marks a file as successfully processed.

        :param file: ProcessedFile domain entity
        :return: True only if exactly one row was updated
        """

        spec = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET status = ?,
                    processed_file_hash = ?,
                    processed_file_name = ?,
                    processed_file_path = ?,
                    processed_file_size = ?,
                    processed_at = ?,
                    error_message = NULL
                WHERE raw_file_hash = ?
            """,
            operation=OperationType.WRITE,
            params=(
                FileStatus.SUCCESS.value,
                file.processed_file_hash,
                file.processed_file_name,
                file.processed_file_path,
                file.processed_file_size,
                file.processed_at,
                file.raw_file_hash
            )
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1

    def get_failed_files(self) -> list[ProcessedFile]:
        """
        Fetch all failed files.
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE status = ?
                ORDER BY last_attempt_at ASC
            """,
            operation=OperationType.READ,
            params=(FileStatus.FAILED.value,),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if not result.data:
            return []

        return [ProcessedFile.from_row(row) for row in result.data]

    def list_unprocessed_files(self) -> list[ProcessedFile]:
        """
        Lists files that still need processing.
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE status IN (?, ?)
                ORDER BY last_attempt_at ASC
            """,
            operation=OperationType.READ,
            params=(FileStatus.PENDING.value),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if not result.data:
            return []

        return [ProcessedFile.from_row(row) for row in result.data]