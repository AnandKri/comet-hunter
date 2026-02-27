from backend.util.constants import DB
from backend.util.enums import FileStatus
from typing import Optional, ClassVar
from backend.database.infrastructure.base import DatabaseBase
from backend.database.domain.processed_file import ProcessedFile

class ProcessedFileRepository(DatabaseBase):
    """
    This class is for `processed_file` table required to keep a log
    of which files are processed and which are not. 
    """
    
    table_name: ClassVar[str] = DB.PROCESSED_FILE

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
                '{FileStatus.PARTIAL.value}','{FileStatus.FAILED.value}')),
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
        
        with self.get_connection() as conn:
            row_created = conn.execute(f"""
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
                """, (
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
                ))
        return row_created.rowcount == 1
    
    def read_file(self):
        pass

    def update_status(self):
        pass

    def delete_file(self):
        pass