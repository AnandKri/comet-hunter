from backend.util.constants import DB
from backend.util.enums import SlotStatus
from typing import Optional, ClassVar
from backend.database.infrastructure.base import DatabaseBase
from datetime import datetime, UTC
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.database.infrastructure.query_spec import QuerySpec

class DownlinkSlotRepository(DatabaseBase):
    """
    This class is for `downlink_slot` table required to monitor/log slots for downlink 
    raw images, as and when they will be available. 
    """

    table_name: ClassVar[str] = DB.DOWNLINK_SLOT

    @classmethod
    def create_table_sql(cls) -> str:
        """
        Query to create `downlink_slot` table 
        """
        return f"""
            CREATE TABLE IF NOT EXISTS {cls.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wk INTEGER NOT NULL,
                doy INTEGER NOT NULL,
                wdy TEXT NOT NULL,
                bot_utc TEXT NOT NULL,
                eot_utc TEXT NOT NULL,
                ant TEXT,
                status TEXT NOT NULL CHECK(status IN ('{SlotStatus.MISSED.value}', 
                '{SlotStatus.PENDING.value}','{SlotStatus.ACTIVE.value}','{SlotStatus.DONE.value}')),
                UNIQUE(wk, doy, bot_utc, ant)
            )
        """
    
    @classmethod
    def create_indexes_sql(cls) -> str:
        """
        Query to create index for `downlink_slot` table
        for faster accessbility while filtering on status and bot_utc 
        """
        return f"""
            CREATE INDEX IF NOT EXISTS idx_schedule_status_time
            ON {cls.table_name} (status, bot_utc)
        """
    
    def create_slot_sql(self, wk: int, doy: int, wdy: str, bot_utc: str, eot_utc: str, 
                    ant: Optional[str], status: SlotStatus) -> QuerySpec:
        """
        Checks if slot status is valid or not.
        Creates the slot details to a row in the table. 
        
        :param wk: Week number of the year
        :param doy: Day number of the year
        :param wdy: Weekday name
        :param bot_utc: Beginning of track, date and time
        :param eot_utc: End of track, date and time
        :param ant: Respective antenna for downlink
        :param status: Status of the slot
        :return: Returns True only if the number of created rows is 1
        """
        
        if not isinstance(status, SlotStatus):
            raise ValueError("status must be SlotStatus enum")
        
        with self.get_connection() as conn:
            row_created = conn.execute(f"""
                INSERT OR IGNORE INTO {self.table_name}
                (wk,doy,wdy,bot_utc,eot_utc,ant,status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    wk, doy, wdy, bot_utc, eot_utc, ant, status.value
                ))
        return row_created.rowcount == 1
    
    def claim_next_slot(self) -> Optional[DownlinkSlot]:
        """
        Gets current running slot if possible
        Update status from `Pending` to `Active`
        :return: Returns complete slot information
        """
        now = str(datetime.now(UTC).isoformat())
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                UPDATE {self.table_name}
                SET status = ?
                WHERE id = (
                    SELECT id
                    FROM {self.table_name}
                    WHERE status = ?
                    AND bot_utc <= ?
                    ORDER BY bot_utc ASC
                    LIMIT 1
                )
                RETURNING *
                """, (SlotStatus.ACTIVE.value,SlotStatus.PENDING.value,now)
                )
        
        row = cursor.fetchone()
        if row:
            return DownlinkSlot.from_row(row)
        return None
        
    def update_status(self, status: SlotStatus, id: int) -> bool:
        """
        Updates slot status for a single slot, located based on 
        slot id value (primary key)

        :param status: New status of the slot
        :param id: primary key
        :return: Returns True only if the number of rows updated is 1
        """
        
        if not isinstance(status, SlotStatus):
            raise ValueError("status must be SlotStatus enum")
        
        with self.get_connection() as conn:
            row_updated = conn.execute(f"""
                UPDATE {self.table_name}
                SET status = ?
                WHERE id = ?
                """,
                (status.value, id))

        return row_updated.rowcount == 1
    
    def delete_slot(self, id: int) -> bool:
        """
        Deletes a `DONE` or `MISSED` slot based on id
        :param id: Primary key
        :return: Returns boolean
        """
        
        with self.get_connection() as conn:
            row_deleted = conn.execute(f"""
                DELETE FROM {self.table_name}
                WHERE id = ?
                AND status IN (?, ?)
                """,
                (id,
                 SlotStatus.DONE.value,
                 SlotStatus.MISSED.value)
                )
        return row_deleted.rowcount == 1