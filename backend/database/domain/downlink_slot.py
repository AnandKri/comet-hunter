from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional
from backend.util.enums import SlotStatus

@dataclass(frozen=True)
class DownlinkSlot:
    """
    Domain entity representing a scheduled downlink window

    Each instance models a single time-bounded slot during which
    raw image data may be received. the slot carries temporal 
    identifiers and its current processing state within the 
    ingestion pipeline

    Invariants:
        - bot_utc and eot_utc must be timezone-aware UTC datetimes
        - bot_utc must be earlier than eot_utc
        - status must be SlotStatus enum value

    Attributes:
        wk: week number of the year.
        doy: Day of year.
        wdy: day of the week.
        bot_utc: Begin-of-transmission time (UTC).
        eot_utc: End-of-transmission time (UTC).
        ant: Antenna identifier (if applicable).
        status: status of the slot.
    
    Invariants:
        - status transitions must contain SlotStatus enum values
    """
    wk: int
    doy: int
    wdy: str
    bot_utc: datetime
    eot_utc: datetime
    ant: Optional[str]
    status: SlotStatus

    def __post_init__(self):

        if self.bot_utc.tzinfo is None:
            raise ValueError("bot_utc must be timezone-aware")

        if self.eot_utc.tzinfo is None:
            raise ValueError("eot_utc must be timezone-aware")
        
        bot_utc = self.bot_utc.astimezone(UTC)
        eot_utc = self.eot_utc.astimezone(UTC)

        object.__setattr__(self, "bot_utc", bot_utc)
        object.__setattr__(self, "eot_utc", eot_utc)

        if bot_utc >= eot_utc:
            raise ValueError("bot_utc must be before eot_utc")
        
        if not isinstance(self.status, SlotStatus):
            raise ValueError("status must be SlotStatus enum")

    @classmethod
    def from_row(cls, row):
        return cls(
            wk=row["wk"],
            doy=row["doy"],
            wdy=row["wdy"],
            bot_utc=datetime.fromisoformat(row["bot_utc"]),
            eot_utc=datetime.fromisoformat(row["eot_utc"]),
            ant=row["ant"],
            status=SlotStatus(row["status"])
        )
    
    def identity(self) -> tuple:
        """
        Natural identity of slot.
        """
        return (self.wk, self.doy, self.wdy, self.bot_utc)