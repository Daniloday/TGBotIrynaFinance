from datetime import datetime, date
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Kyiv")


def dt_local(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=TZ)


def date_local(ts: int) -> date:
    return dt_local(ts).date()


def fmt_time(ts: int) -> str:
    return dt_local(ts).strftime("%H:%M")
