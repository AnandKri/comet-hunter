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

class JobStatus(Enum):
    """
    Contains Enum values for status of 
    background jobs.
    """
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    def __str__(self):
        return self.value

class JobType(Enum):
    """
    Contains Enum values for type of 
    background jobs.
    """
    SYNC_SLOTS = "SYNC_SLOTS"
    SYNC_PROCESSED_FRAMES = "SYNC_PROCESSED_FRAMES"
    GET_PROCESSED_FRAMES = "GET_PROCESSED_FRAMES"
    START_SCHEDULER = "START_SCHEDULER"

    def __str__(self):
        return self.value

class JobEventType(str, Enum):
    JOB_RUNNING = "job.running"
    JOB_QUEUED = "job.queued"
    JOB_COMPLETED = "job.completed"
    JOB_CANCELLED = "job.cancelled"
    JOB_FAILED = "job.failed"

    SLOTS_SYNCED = "slots.synced"

    METADATA_SYNCED = "metadata.synced"
    DOWNLOAD_RECOVER = "download.recover"
    DOWNLOAD_COMPLETED = "download.completed"

    PROCESS_RECOVER = "process.recover"
    PROCESS_READY = "process.ready"
    PROCESS_COMPLETED = "process.completed"
    
    SLOT_ACTIVE = "slot.active"
    CYCLE_COMPLETED = "cycle.completed"