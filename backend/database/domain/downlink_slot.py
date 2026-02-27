from dataclasses import dataclass
from typing import Optional
from util.enums import SlotStatus

@dataclass
class DownlinkSlot:
    id: int
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
            id=row["id"],
            wk=row["wk"],
            doy=row["doy"],
            wdy=row["wdy"],
            bot_utc=row["bot_utc"],
            eot_utc=row["eot_utc"],
            ant=row["ant"],
            status=SlotStatus(row["status"])
        )