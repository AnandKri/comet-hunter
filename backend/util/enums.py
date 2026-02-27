from enum import Enum

class SlotStatus(Enum):
    """
    Contains Enum values for status of slots
    """
    MISSED = "MISSED"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DONE = "DONE"

class FileStatus(Enum):
    """
    Contains Enum values for various status
    of file being processed 
    """
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"