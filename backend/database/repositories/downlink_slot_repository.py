from backend.util.constants import DB
from backend.util.enums import SlotStatus,FetchType,OperationType
from typing import Optional, ClassVar
from datetime import datetime, UTC
from backend.database.domain.downlink_slot import DownlinkSlot
from backend.database.infrastructure.query_spec import QuerySpec
from backend.database.infrastructure.query_executor import QueryExecutor
from dataclasses import replace

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
    
    def create_slot(self, slot: DownlinkSlot) -> bool:
        """
        Checks if slot status is valid or not.
        Creates the slot details to a row in the table. 
        
        :param slot: DownlinkSlot domain object
        :return: True only if the number of created rows is 1
        """
        
        if not isinstance(slot.status, SlotStatus):
            raise ValueError("status must be SlotStatus enum")
        
        spec = QuerySpec(
            sql=f"""
                INSERT OR IGNORE INTO {self.table_name}
                (wk,doy,wdy,bot_utc,eot_utc,ant,status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            operation=OperationType.WRITE,
            params=(slot.wk, slot.doy, slot.wdy, slot.bot_utc, slot.eot_utc, slot.ant, slot.status.value)
        )

        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def mark_expired_pending_as_missed(self, now: str) -> int:
        """
        Marks all expired PENDING slots as MISSED.

        A slot is considered expired if its `eot_utc` is earlier than the
        provided timestamp. Only slots in PENDING state are transitioned,
        ensuring that ACTIVE and DONE slots are not affected.

        This method is typically invoked during synchronization or scheduler
        initialization to clean up stale, unclaimed slots.

        The comparison relies on ISO 8601 UTC string ordering, so `now` must
        be provided in ISO format (e.g. "2026-04-11T12:00:00+00:00").

        :param now: Current timestamp (UTC, ISO format) used as cutoff.
        :return: Number of rows updated (slots marked as MISSED).
        """

        spec = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET status = ?
                WHERE eot_utc < ?
                AND status = ?
            """,
            operation=OperationType.WRITE,
            params=(
                SlotStatus.MISSED.value,
                now,
                SlotStatus.PENDING.value
            )
        )

        result = self._executor.execute(spec)

        return result.rows_affected
    
    def mark_expired_active_as_missed(self, now: str) -> int:
        """
        Mark all expired ACTIVE slots as MISSED.

        A slot is considered expired if its `eot_utc` is earlier than the provided
        timestamp. Only slots currently in ACTIVE state are transitioned to MISSED.
        This is typically used during system startup or synchronization to recover
        from crashes or incomplete lifecycle transitions.

        This ensures that stale ACTIVE slots (which were not marked DONE due to
        interruptions) do not remain indefinitely ACTIVE.

        :param now: Current timestamp in ISO UTC format.
        :return: Number of slots updated.
        """

        spec = QuerySpec(
            sql=f"""
                UPDATE {self.table_name}
                SET status = ?
                WHERE eot_utc < ?
                AND status = ?
            """,
            operation=OperationType.WRITE,
            params=(
                SlotStatus.MISSED.value,
                now,
                SlotStatus.ACTIVE.value
            )
        )

        result = self._executor.execute(spec)

        return result.rows_affected

    def get_next_claimable_slot(self, now: str) -> Optional[DownlinkSlot]:
        """
        Fetch the next eligible PENDING slot that can be activated.

        A slot is considered claimable if:
        - its status is PENDING
        - its time window includes the current timestamp (`bot_utc <= now <= eot_utc`)

        Among all eligible slots, the earliest slot (based on `bot_utc`) is selected
        to ensure deterministic and sequential processing.

        This method performs a read-only operation and does not mutate state.

        :param now: Current timestamp in ISO UTC format.
        :return: Next claimable DownlinkSlot if available, else None.
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE status = ?
                AND bot_utc <= ?
                AND eot_utc >= ?
                ORDER BY bot_utc ASC
                LIMIT 1
            """,
            operation=OperationType.READ,
            params=(
                SlotStatus.PENDING.value,
                now,
                now
            ),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        if not result.data:
            return None

        return DownlinkSlot.from_row(result.data)
        
    def update_status(self, newStatus: SlotStatus, slot: DownlinkSlot) -> Optional[DownlinkSlot]:
        """
        Updates slot status for a single slot, using its domain identity

        :param newStatus: New status of the slot
        :param slot: Slot whose identity is used for lookup
        :return: updated slot domain entity (with updated slot) if successful
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

        if result.rows_affected == 1:
            return replace(slot, status=newStatus)
    
    def delete_slot(self, slot: DownlinkSlot) -> bool:
        """
        Deletes a slot
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
                """,
            operation=OperationType.WRITE,
            params=(slot.wk,
                    slot.doy,
                    slot.wdy,
                    slot.bot_utc)
        )
        
        result = self._executor.execute(spec)

        return result.rows_affected == 1
    
    def delete_completed_slots(self) -> int:
        """
        Deletes all slots whose status is `DONE`.
        :return: Number of rows deleted
        """

        spec = QuerySpec(
            sql=f"""
                DELETE FROM {self.table_name}
                WHERE status = ?
            """,
            operation=OperationType.WRITE,
            params=(
                SlotStatus.DONE.value
            )
        )

        result = self._executor.execute(spec)

        return result.rows_affected
    
    def exists(self, identity: tuple) -> bool:
        """
        Checks if slot exists in the DB or not

        :param identity: Natural identity of a slot
        :return: True if slot exists. False Otherwise
        """

        wk, doy, wdy, bot_utc = identity

        spec = QuerySpec(
            sql=f"""
                SELECT 1
                FROM {self.table_name}
                WHERE wk = ?
                AND doy = ?
                AND wdy = ?
                AND bot_utc = ?
                LIMIT 1
            """,
            operation=OperationType.READ,
            params=(wk, doy, wdy, bot_utc),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        return result.data is not None
    
    def get_recent_slots(self, since: str, now: str) -> list[DownlinkSlot]:
        """
        Fetch slots overlapping the time window [since, now], excluding future
        or not-yet-activated (PENDING) slots.

        This method returns slots whose time window intersects with the given
        interval and are already ACTIVE, DONE, or MISSED. It avoids returning
        future scheduled (PENDING) slots.

        The comparison is performed lexicographically on ISO 8601 UTC strings,
        so `since` must be in ISO format (e.g. "2026-04-11T12:00:00+00:00").

        :param since: Lower bound timestamp (inclusive) in ISO UTC format.
        :param now: upper bound timestamp (inclusive) in ISO UTC format. 
        expected to be current timestamp, but could be anything
        :return: List of DownlinkSlot domain entities ordered by `bot_utc`.
        """

        since_dt = datetime.fromisoformat(since)
        now_dt = datetime.fromisoformat(now)

        if since_dt >= now_dt:
            raise ValueError("`since` must be earlier than `now`")

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE bot_utc <= ?
                AND eot_utc >= ?
                AND status IN (?, ?, ?)
                ORDER BY bot_utc ASC
            """,
            operation=OperationType.READ,
            params=(
                now,
                since,
                SlotStatus.ACTIVE.value,
                SlotStatus.DONE.value,
                SlotStatus.MISSED.value
            ),
            fetch=FetchType.ALL
        )

        result = self._executor.execute(spec)

        if not result.data:
            return []

        return [DownlinkSlot.from_row(row) for row in result.data]
    
    def get_active_slot(self) -> Optional[DownlinkSlot]:
        """
        Fetch latest ACTIVE slot if present.

        No state mutation is performed. This method is a pure read.

        :return: Active DownlinkSlot if exists, else None.
        """

        spec = QuerySpec(
            sql=f"""
                SELECT *
                FROM {self.table_name}
                WHERE status = ?
                ORDER BY bot_utc DESC
                LIMIT 1
            """,
            operation=OperationType.READ,
            params=(SlotStatus.ACTIVE.value,),
            fetch=FetchType.ONE
        )

        result = self._executor.execute(spec)

        if not result.data:
            return None

        return DownlinkSlot.from_row(result.data)