from dataclasses import dataclass, replace
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional
from backend.util.enums import FileStatus, Instrument

@dataclass(frozen=True)
class ProcessedFile:
    """
    Domain entity representing the processing state of a raw image file.

    Tracks the transformation of a raw file into its processed output,
    including hash integrity, storage paths, retry attempts, and lifecycle
    status within the pipeline.

    Attributes:
        raw_file_name: Original raw file name - primary key.
        raw_file_hash: Content hash of the original raw file.
        raw_file_path: Storage path of the raw file.
        raw_file_size: Size of the raw file in bytes.
        processed_file_name: Processed file name.
        processed_file_hash: Content hash of the processed file.
        processed_file_path: Storage path of the processed file.
        processed_file_size: Size of the processed file in bytes.
        datetime_of_observation: date time of observation
        instrument: Instrument used for obesrvation
        status: Current processing lifecycle state.
        error_message: Error details if processing failed.
        downloaded_at: UTC timestamp when file downloaded.
        last_downloading_attempt_at: UTC timestamp of the most recent downloading attempt.
        downloading_attempt_count: Number of downloading attempts made.
        processed_at: UTC timestamp when processing completed.
        last_processing_attempt_at: UTC timestamp of the most recent processing attempt.
        processing_attempt_count: Number of processing attempts made.
        previous_file_name: previous file name which will help in processing

    Invariants:
        - status value is one of the FileStatus enums
    """
    raw_file_name: str
    raw_file_hash: Optional[str]
    raw_file_path: Optional[Path]
    raw_file_size: Optional[int]
    processed_file_name: Optional[str]
    processed_file_hash: Optional[str]
    processed_file_path: Optional[Path]
    processed_file_size: Optional[int]
    datetime_of_observation: datetime
    instrument: Instrument
    status: FileStatus
    error_message: Optional[str]
    downloaded_at: Optional[datetime]
    last_downloading_attempt_at: Optional[datetime]
    downloading_attempt_count: int
    processed_at: Optional[datetime]
    last_processing_attempt_at: Optional[datetime]
    processing_attempt_count: int
    previous_file_name: Optional[str]

    VALID_TRANSITIONS = {
        FileStatus.DISCOVERED: {FileStatus.DOWNLOADING,
                                FileStatus.DOWNLOADED},
        FileStatus.DOWNLOADING: {FileStatus.DOWNLOADING_FAILED,
                                 FileStatus.DOWNLOADED},
        FileStatus.DOWNLOADING_FAILED: {FileStatus.DOWNLOADING,
                                        FileStatus.IGNORE},
        FileStatus.DOWNLOADED: {FileStatus.DOWNLOADING_FAILED,
                                FileStatus.READY,
                                FileStatus.SKIPPED},
        FileStatus.READY: {FileStatus.PROCESSING},
        FileStatus.PROCESSING: {FileStatus.PROCESSING_FAILED,
                                FileStatus.PROCESSED},
        FileStatus.PROCESSING_FAILED: {FileStatus.PROCESSING,
                                       FileStatus.ABANDONED},
        FileStatus.IGNORE: set(),
        FileStatus.SKIPPED: set(),
        FileStatus.ABANDONED: set(),
        FileStatus.PROCESSED: set(),
    }

    def __post_init__(self):

        self._validate_datetime(
            "datetime_of_observation", 
            self.datetime_of_observation
        )

        object.__setattr__(
            self, 
            "datetime_of_observation", 
            self.datetime_of_observation.astimezone(UTC)
        )

        optional_datetimes = [
            "downloaded_at",
            "last_downloading_attempt_at",
            "processed_at",
            "last_processing_attempt_at"
        ]

        for field_name in optional_datetimes:
            datetime_value = getattr(self, field_name)
            if datetime_value is not None:
                self._validate_datetime(field_name, datetime_value)
                object.__setattr__(
                    self,
                    field_name,
                    datetime_value.astimezone(UTC)
                )
        if not isinstance(self.instrument, Instrument):
            raise ValueError("instrument must be Instrument enum")
        if not isinstance(self.status, FileStatus):
            raise ValueError("status must be FileStatus enum")
        if self.downloading_attempt_count < 0:
            raise ValueError("downloading_attempt_count must be non-negative")
        if self.processing_attempt_count < 0:
            raise ValueError("processing_attempt_count must be non-negative")
        if self.raw_file_size is not None and self.raw_file_size < 0:
            raise ValueError("raw_file_size must be non-negative")
        if self.processed_file_size is not None and self.processed_file_size < 0:
            raise ValueError("processed_file_size must be non-negative")

    @staticmethod
    def _validate_datetime(field_name: str, value: datetime) -> None:
        if value.tzinfo is None:
            raise ValueError(f"{field_name} must be timezone-aware")
    
    def can_transition(self, new_status: FileStatus) -> bool:
        """
        Checks if file can legally transition from its current status
        to given new status based on the lifecycle state machine.

        :param new_status: Target status to validate transition against
        :return: True if transition is allowed. False otherwise
        """
        return new_status in self.VALID_TRANSITIONS.get(self.status, set())
    
    def transition_to(self, new_status: FileStatus) -> "ProcessedFile":
        """
        Creates a new immutable ProcessedFile instance with updated status
        after validating that the transition is allowed.

        :param new_status: Target lifecycle status
        :return: New instance with updated status
        Raises:
            ValueError: If transition is not allowed by the lifecycle rules.
        """
        if not self.can_transition(new_status):
            raise ValueError(f"Invalid transition {self.status} -> {new_status}")
        
        return replace(self, status=new_status)
    
    def is_terminal(self) -> bool:
        """
        checks if current status of the file is terminal lifecycle
        status or not.
        Terminal states indicate no further processing or retries will
        occur.
        
        :return: True if file is in terminal state. False otherwise
        """
        return self.status in {
            FileStatus.IGNORE, 
            FileStatus.SKIPPED, 
            FileStatus.ABANDONED, 
            FileStatus.PROCESSED
        }
    
    def can_retry_processing(self, max_processing_attempts: int) -> bool:
        """
        Determines whether processing can be retried based on attempt limits
        :param max_processing_attempts: Maximum allowed processing attempts.
        :returns: True if processing retry is allowed False otherwise.
        """
        return (self.status == FileStatus.PROCESSING_FAILED) and (self.processing_attempt_count < max_processing_attempts)
    
    def can_retry_downloading(self, max_downloading_attempts: int) -> bool:
        """
        Determines whether downloading can be retried based on attempt limits
        :param max_downloading_attempts: Maximum allowed download attempts.
        :return: True if download retry is allowed False otherwise.
        """
        return (self.status == FileStatus.DOWNLOADING_FAILED) and (self.downloading_attempt_count < max_downloading_attempts)
    
    def is_download_complete(self) -> bool:
        """
        Checks whether the raw file has been successfully downloaded
        and is ready for further pipeline decisions.

        A file is considered download complete if it has reached
        `DOWNLOADED` state.

        :return: True if file status is DOWNLOADED, False otherwise.
        """

        return self.status == FileStatus.DOWNLOADED

    def identity(self) -> str:
        """
        Returns the unique identity of the processed file domain entity.

        The raw file name acts as the natural identity since it uniquely
        represents the source file across the pipeline.

        :returns: Raw file name (primary identity).
        """

        return self.raw_file_name

    @classmethod
    def from_row(cls, row: dict) -> "ProcessedFile":
        """
        Creates a ProcessedFile domain entity from a database row.
        
        :param row: Database row containing processed_file table data.
        :return: Constructed domain entity populated from DB row.
        """
        return cls(
            raw_file_name=row["raw_file_name"],
            raw_file_hash=row["raw_file_hash"],
            raw_file_path=(Path(row["raw_file_path"]) if row["raw_file_path"] else None),
            raw_file_size=row["raw_file_size"],
            processed_file_name=row["processed_file_name"],
            processed_file_hash=row["processed_file_hash"],
            processed_file_path=(Path(row["processed_file_path"]) if row["processed_file_path"] else None),
            processed_file_size=row["processed_file_size"],
            datetime_of_observation=datetime.fromisoformat(row["datetime_of_observation"]),
            instrument=Instrument(row["instrument"]),
            status=FileStatus(row["status"]),
            error_message=row["error_message"],
            downloaded_at=(datetime.fromisoformat(row["downloaded_at"]) if row["downloaded_at"] else None),
            last_downloading_attempt_at=(datetime.fromisoformat(row["last_downloading_attempt_at"]) if row["last_downloading_attempt_at"] else None),
            downloading_attempt_count=row["downloading_attempt_count"],
            processed_at=(datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None),
            last_processing_attempt_at=(datetime.fromisoformat(row["last_processing_attempt_at"]) if row["last_processing_attempt_at"] else None),
            processing_attempt_count=row["processing_attempt_count"],
            previous_file_name=row["previous_file_name"]
        )