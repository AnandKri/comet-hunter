from enum import Enum

class SlotStatus(Enum):
    """
    Contains Enum values for status of slots
    """
    MISSED = "MISSED"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DONE = "DONE"

    def __str__(self):
        return self.value

class FileStatus(Enum):
    """
    Contains Enum values for various status
    of file being processed 
    """
    DISCOVERED = "DISCOVERED"
    DOWNLOADING = "DOWNLOADING"
    DOWNLOADED = "DOWNLOADED"
    DOWNLOADING_FAILED = "DOWNLOADING_FAILED"
    IGNORE = "IGNORE"
    SKIPPED = "SKIPPED"
    READY = "READY"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    ABANDONED = "ABANDONED"

    def __str__(self):
        return self.value

class FetchType(Enum):
    """
    Contains Enum values for fetching number
    of rows when executing a read query
    """
    ONE = "one"
    ALL = "all"

    def __str__(self):
        return self.value

class OperationType(Enum):
    """
    Contains Enum values for type of query
    `read` which is SELECT or `write` which
    covers UPDATE, DELETE, and INSERT queries
    """
    READ = "read"
    WRITE = "write"

    def __str__(self):
        return self.value

class Instrument(Enum):
    """
    Contains Enum values for type of 
    coronagraphs available for LASCO
    """
    C2 = "c2"
    C3 = "c3"

    def __str__(self):
        return self.value