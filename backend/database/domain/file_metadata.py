from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class FileMetadata:
    """
    Domain entity representing a file metadata

    Each instance models a metadata of a single file.
    Metadata contains file name, datetime of observation,
    instrument used for observation, exposure time, pixel
    numbers in width and height, roll angle

    Attributes:
        raw_file_name: raw file name as present in the data 
        raw_file_hash: calculated file hash value, will be null initially
        datetime_of_observation: date and time of observation
        instrument: instrument used for observation
        exposure_time: exposure time for taking the image
        width: number of pixels
        height: number of pixels
        roll: roll angle of camera while taking the observation
    """
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