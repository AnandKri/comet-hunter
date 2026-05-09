from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional
from backend.util.enums import Instrument

@dataclass(frozen=True)
class FileMetadata:
    """
    Domain entity representing a file metadata

    Each instance models a metadata of a single file.
    Metadata contains file name, datetime of observation,
    instrument used for observation, exposure time, pixel
    numbers in width and height, roll angle

    Invariants:
        - datetime fields must be timezone-aware UTC datetimes
        - instrument must be Instrument enum
        - exposure_time must be positive
        - width and height must be positive integers

    Attributes:
        raw_file_name: raw file name as present in the data 
        raw_file_hash: calculated file hash value, will be null initially
        datetime_of_observation: date and time of observation
        last_modified_utc : date time when the file became available 
        instrument: instrument used for observation
        exposure_time: exposure time for taking the image
        width: number of pixels
        height: number of pixels
        roll: roll angle of camera while taking the observation
    """
    raw_file_name: str 
    raw_file_hash: Optional[str]
    datetime_of_observation: datetime
    last_modified_utc : datetime
    instrument: Instrument
    exposure_time: float 
    width: int
    height: int
    roll: float

    def __post_init__(self):
        if self.datetime_of_observation.tzinfo is None:
            raise ValueError("datetime_of_observation must be timezone-aware")

        if self.last_modified_utc.tzinfo is None:
            raise ValueError("last_modified_utc must be timezone-aware")
        
        object.__setattr__(self, "datetime_of_observation", self.datetime_of_observation.astimezone(UTC))
        object.__setattr__(self, "last_modified_utc", self.last_modified_utc.astimezone(UTC))

        if not isinstance(self.instrument, Instrument):
            raise ValueError("instrument must be Instrument enum")

        if self.exposure_time <= 0:
            raise ValueError("exposure_time must be a positive value")

        if self.width <= 0:
            raise ValueError("width must be a positive integer")
        
        if self.height <= 0:
            raise ValueError("height must be a positive integer")

    @classmethod
    def from_row(cls, row):
        return cls(
            raw_file_name = row["raw_file_name"],
            raw_file_hash = row["raw_file_hash"],
            datetime_of_observation = datetime.fromisoformat(row["datetime_of_observation"]),
            last_modified_utc = datetime.fromisoformat(row["last_modified_utc"]),
            instrument = Instrument(row["instrument"]),
            exposure_time = row["exposure_time"], 
            width = row["width"],
            height = row["height"], 
            roll = row["roll"]
        )