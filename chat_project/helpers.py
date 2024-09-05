from datetime import datetime
from zoneinfo import ZoneInfo

SEOUL_TZ = ZoneInfo("Asia/Seoul")


def datetime_to_str(dt: datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S")
