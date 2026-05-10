from datetime import datetime, UTC

def validate_time_window(start: datetime, end: datetime):
    if start >= end:
        raise ValueError("start must be earlier than end")

def to_utc(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

def parse_utc_datetime(dt_str: str) -> datetime:
    """
    Parse ISO datetime string into timezone-aware UTC datetime.

    Rules:
    - naive datetimes are assumed to be UTC
    - timezone-aware datetimes are normalized to UTC
    """

    dt = datetime.fromisoformat(dt_str)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    return dt.astimezone(UTC)