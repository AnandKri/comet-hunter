from datetime import datetime, timezone

def validate_time_window(start: datetime, end: datetime):
    if start >= end:
        raise ValueError("start must be earlier than end")

def _to_utc(dt_str: str):
    dt = datetime.fromisoformat(dt_str)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)