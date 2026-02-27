from backend.util.constants import DB
from typing import Optional, ClassVar
from backend.database.infrastructure.base import DatabaseBase
from backend.database.domain.file_metadata import FileMetadata

class FileMetadataRepository(DatabaseBase):
    """
    This class is for `file_metadata` table required to keep a log
    of file metadata, useful beforehand while retrieving the raw data.
    """
    
    table_name: ClassVar[str] = DB.FILE_METADATA

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
        for faster accessbility while filtering based on instrument 
        and date_of_observation.
        """
        return f"""
            CREATE INDEX IF NOT EXISTS idx_file_metadata_time
            ON {cls.table_name} (instrument, datetime_of_observation)
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
        with self.get_connection() as conn:
            row_created = conn.execute(f"""
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
                """, (
                    raw_file_name, 
                    raw_file_hash, 
                    datetime_of_observation,
                    instrument,
                    exposure_time, 
                    width, 
                    height, 
                    roll
                ))
        return row_created.rowcount == 1
    
    def read_metadata(self):
        pass

    def update_metadata(self):
        pass

    def delete_metadata(self):
        pass