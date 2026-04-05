from dataclasses import dataclass
from typing import Optional
from util.enums import SlotStatus

@dataclass(frozen=True)
class DownlinkSlot:
    """
    Domain entity representing a scheduled downlink window

    Each instance models a single time-bounded slot during which
    raw image data may be received. the slot carries temporal 
    identifiers and its current processing state within the 
    ingestion pipeline

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
    bot_utc: str
    eot_utc: str
    ant: Optional[str]
    status: SlotStatus

    @classmethod
    def from_row(cls, row):
        return cls(
            wk=row["wk"],
            doy=row["doy"],
            wdy=row["wdy"],
            bot_utc=row["bot_utc"],
            eot_utc=row["eot_utc"],
            ant=row["ant"],
            status=SlotStatus(row["status"])
        )
    
    def identity(self) -> tuple:
        """
        Natural identity of slot.
        """
        return (self.wk, self.doy, self.wdy, self.bot_utc)