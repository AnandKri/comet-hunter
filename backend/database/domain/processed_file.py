from dataclasses import dataclass
from typing import Optional
from util.enums import FileStatus

@dataclass(frozen=True)
class ProcessedFile:
    """
    Domain entity representing the processing state of a raw image file.

    Tracks the transformation of a raw file into its processed output,
    including hash integrity, storage paths, retry attempts, and lifecycle
    status within the pipeline.

    Attributes:
        raw_file_hash: Content hash of the original raw file.
        raw_file_name: Original raw file name.
        raw_file_path: Storage path of the raw file.
        raw_file_size: Size of the raw file in bytes.

        processed_file_hash: Content hash of the processed file.
        processed_file_name: Processed file name.
        processed_file_path: Storage path of the processed file.
        processed_file_size: Size of the processed file in bytes.

        status: Current processing lifecycle state.
        error_message: Error details if processing failed.
        processed_at: UTC timestamp when processing completed.
        last_attempt_at: UTC timestamp of the most recent processing attempt.
        attempt_count: Number of processing attempts made.

    Invariants:
        - status value is one of the FileStatus enums
    """
    raw_file_hash: str
    raw_file_name: str
    raw_file_path: str
    raw_file_size: Optional[int]
    processed_file_hash: str
    processed_file_name: str
    processed_file_path: str
    processed_file_size: str
    status: FileStatus
    error_message: Optional[str]
    processed_at: Optional[str]
    last_attempt_at: str
    attempt_count: int

    @classmethod
    def from_row(cls, row):
        return cls(
            raw_file_hash=row["raw_file_hash"],
            raw_file_name=row["raw_file_name"],
            raw_file_path=row["raw_file_path"],
            raw_file_size=row["raw_file_size"],
            processed_file_hash=row["processed_file_hash"],
            processed_file_name=row["processed_file_name"],
            processed_file_path=row["processed_file_path"],
            processed_file_size=row["processed_file_size"],
            status=FileStatus(row["status"]),
            error_message=row["error_message"],
            processed_at=row["processed_at"],
            last_attempt_at=row["last_attempt_at"],
            attempt_count=row["attempt_count"]
        )