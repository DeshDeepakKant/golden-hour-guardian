"""Small shared helpers: ids, UTC/IST time, INR formatting."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def aware(dt: datetime) -> datetime:
    """Treat naive datetimes as UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def parse_ts(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return aware(value)
    return aware(datetime.fromisoformat(value.replace("Z", "+00:00")))


def to_ist(dt: datetime) -> datetime:
    return aware(dt).astimezone(IST)


def fmt_ist(dt: datetime) -> str:
    return to_ist(dt).strftime("%d %b %Y, %H:%M IST")


def fmt_inr(paise: int) -> str:
    """Integer paise -> '₹24,999' (Indian digit grouping). Only used at the edges."""
    rupees, rem = divmod(abs(int(paise)), 100)
    s = str(rupees)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups + [tail])
    out = f"₹{s}" + (f".{rem:02d}" if rem else "")
    return ("-" + out) if paise < 0 else out
