from datetime import datetime, timezone

def validate_time_window(start: str, end: str):
    s = _to_utc(start)
    e = _to_utc(end)
    if s >= e:
        raise ValueError("start must be earlier than end")

def _to_utc(dt_str: str):
    dt = datetime.fromisoformat(dt_str)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)