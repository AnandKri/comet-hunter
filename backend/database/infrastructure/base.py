import sqlite3
from backend.util.constants import DB
from pathlib import Path
from typing import ClassVar, Optional
# from backend.database.repositories.downlink_slot_repository import DownlinkSlotRepository
# from backend.database.repositories.file_metadata_repository import FileMetadataRepository
# from backend.database.repositories.processed_file_repository import ProcessedFileRepository

class DatabaseBase:
    """
    Infrastructure layer for SQLite access
    Handles:
    - Database file creation
    - connection management

    Class Attributes:
        _db_path (Path): Filesystem path where the database is supposed to be.
    """
    
    _db_path: ClassVar[Optional[Path]] = None
    
    @classmethod
    def initialize_database(cls) -> None:
        """
        Explicitly initialize the database
        Must be called at application startup
        """
        if cls._db_path is None:
            cls._db_path = Path(f"{DB.NAME}.db")
            cls._db_path.touch(exist_ok=True)
        
            with sqlite3.connect(cls._db_path) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
    
    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """
        Creates and returns a new SQLite connection.

        - Enables foreign key constraints.
        - Caller is responsible for closing the connection.

        Raises:
            AssertionError: If there's an attempt to make connection
            before database initialization (indirectly). Directly, it checks
            that filesystem path for database should not be none.

        :return: connection to database
        :rtype: sqlite3.Connection
        """

        assert cls._db_path is not None, "Database filesystem path is not initialized"

        conn = sqlite3.connect(
            cls._db_path, 
            timeout=30, 
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn