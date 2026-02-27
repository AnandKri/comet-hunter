from dataclasses import dataclass
from typing import Optional

@dataclass
class FileMetadata:
    raw_file_name: str 
    raw_file_hash: Optional[str]
    datetime_of_observation: str
    instrument: str
    exposure_time: float 
    width: int
    height: int 
    roll: float

    @classmethod
    def from_row(cls, row):
        return cls(
            raw_file_name = row["raw_file_name"],
            raw_file_hash = row["raw_file_hash"],
            datetime_of_observation = row["datetime_of_observation"],
            instrument = row["instrument"],
            exposure_time = row["exposure_time"], 
            width = row["width"],
            height = row["height"], 
            roll = row["roll"]
        )