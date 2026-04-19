from datetime import datetime

def validate_time_window(start: str, end: str):
    s = datetime.fromisoformat(start)
    e = datetime.fromisoformat(end)
    if s >= e:
        raise ValueError("start must be earlier than end")