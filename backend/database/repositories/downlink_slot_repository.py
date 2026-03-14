from backend.util.constants import DB
from backend.util.enums import SlotStatus,FetchType,OperationType
from typing import Optional, ClassVar
from datetime import datetime, UTC
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.database.infrastructure.query_spec import QuerySpec
from backend.database.infrastructure.query_executor import QueryExecutor


class DownlinkSlotRepository:
    """
    This class is for `downlink_slot` table required to monitor/log slots for downlink 
    raw images, as and when they will be available. 
    """

    table_name: ClassVar[str] = DB.DOWNLINK_SLOT

    def __init__(self, executor: QueryExecutor):
        self._executor = executor
    
    @classmethod
    def create_table_sql(cls) -> str:
        """
        Query to create `downlink_slot` table 
        """
        return f"""
            CREATE TABLE IF NOT EXISTS {cls.table_name} (
                wk INTEGER NOT NULL,
                doy INTEGER NOT NULL,
                wdy TEXT NOT NULL,
                bot_utc TEXT NOT NULL,
                eot_utc TEXT NOT NULL,
                ant TEXT,
                status TEXT NOT NULL CHECK(status IN ('{SlotStatus.MISSED.value}', 
                '{SlotStatus.PENDING.value}','{SlotStatus.ACTIVE.value}','{SlotStatus.DONE.value}')),
                PRIMARY KEY (wk, doy, wdy, bot_utc)
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
    
    def create_slot(self, wk: int, doy: int, wdy: str, bot_utc: str, eot_utc: str, 
                    ant: Optional[str], status: SlotStatus) -> bool:
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
        
        spec = QuerySpec(
            sql=f"""
                INSERT OR IGNORE INTO {self.table_name}
                (wk,doy,wdy,bot_utc,eot_utc,ant,status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            operation=OperationType.WRITE,
            params=(wk, doy, wdy, bot_utc, eot_utc, ant, status.value)
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def get_current_active_slot(self) -> Optional[DownlinkSlot]:
        """
        1. Marks expired slots as `MISSED` (Mandatory Step)
        2. Gets `ACTIVE` slot if present
        3. If `ACTIVE` slot is not present then
        Gets logically Active slots and Updates its status 
        from `PENDING` to `ACTIVE`
        :return: Returns complete slot information
        """
        now = str(datetime.now(UTC).isoformat())

        cleanup = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET status = ?
                WHERE eot_utc < ?
                AND status IN (?, ?)
                """,
            operation=OperationType.WRITE,
            params=(SlotStatus.MISSED.value,
                    now,
                    SlotStatus.PENDING.value,
                    SlotStatus.ACTIVE.value)
        )
        _ = self._executor.execute(cleanup)

        active_spec = QuerySpec(
            sql = f"""
                SELECT *
                FROM {self.table_name}
                WHERE status = ?
                AND bot_utc <= ?
                AND eot_utc >= ?
                LIMIT 1
                """,
            operation=OperationType.READ,
            params=(
                SlotStatus.ACTIVE.value,
                now,
                now
            ),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(active_spec)

        if result.data:
            return DownlinkSlot.from_row(result.data)
        
        claim_spec = QuerySpec(
            sql = f"""
                SELECT *
                FROM {self.table_name}
                WHERE status = ?
                AND bot_utc <= ?
                AND eot_utc >= ?
                ORDER BY bot_utc ASC
                LIMIT 1
                """,
            operation=OperationType.READ,
            params=(SlotStatus.PENDING.value,
                    now,
                    now),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(claim_spec)

        if result.data is None:
            return None
        
        claimed_slot = DownlinkSlot.from_row(result.data)

        self.update_status(newStatus = SlotStatus.ACTIVE.value, slot = claimed_slot)
        
        return claimed_slot
        
    def update_status(self, newStatus: SlotStatus, slot: DownlinkSlot) -> bool:
        """
        Updates slot status for a single slot, using its domain identity

        :param newStatus: New status of the slot
        :param slot: Slot whose identity is used for lookup
        :return: True only if exactly one row was updated
        """
        
        if not isinstance(newStatus, SlotStatus):
            raise ValueError("status must be SlotStatus enum")
        
        spec = QuerySpec(
            sql = f"""
                UPDATE {self.table_name}
                SET status = ?
                WHERE wk = ?
                AND doy = ?
                AND wdy = ?
                AND bot_utc = ?
                """,
            operation = OperationType.WRITE,
            params = (newStatus.value,
                      slot.wk,
                      slot.doy,
                      slot.wdy,
                      slot.bot_utc) 
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def delete_slot(self, slot: DownlinkSlot) -> bool:
        """
        Deletes a `DONE` or `MISSED` slot based on its domain identity
        :param slot: Slot whose identity is used for lookup
        :return: True only if exactly one row was delete
        """

        spec = QuerySpec(
            sql = f"""
                DELETE FROM {self.table_name}
                WHERE wk = ?
                AND doy = ?
                AND wdy = ?
                AND bot_utc = ?
                AND status IN (?, ?)
                """,
            operation=OperationType.WRITE,
            params=(slot.wk,
                    slot.doy,
                    slot.wdy,
                    slot.bot_utc,
                    SlotStatus.DONE.value,
                    SlotStatus.MISSED.value)
        )
        
        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def delete_completed_slots(self) -> int:
        """
        Deletes all slots whose status is `DONE` or `MISSED`.
        :return: Number of rows deleted
        """

        spec = QuerySpec(
            sql=f"""
                DELETE FROM {self.table_name}
                WHERE status IN (?, ?)
            """,
            operation=OperationType.WRITE,
            params=(
                SlotStatus.DONE.value,
                SlotStatus.MISSED.value
            )
        )

        result = self._executor.execute(spec)

        return result.rows_affected