from datetime import datetime, time
from zoneinfo import ZoneInfo


def parse_session_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def now_in_timezone(timezone_name: str) -> datetime:
    return datetime.now(tz=ZoneInfo(timezone_name))
