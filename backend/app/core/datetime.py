from datetime import datetime, time, timezone

DATE_KEYS = (
    "recordTime",
    "meetingDate",
    "receivedDate",
    "sentDate",
    "documentDate",
    "occurredAt",
    "archivedAt",
    "deletedAt",
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_instant(value: str | None, *, end_of_day: bool = False) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
            day = datetime.fromisoformat(raw[:10]).date()
            rest = raw[10:]
            if not rest or rest[0] != "T":
                clock = time(23, 59, 59) if end_of_day else time(0, 0)
                return datetime.combine(day, clock, tzinfo=timezone.utc)
            iso = raw.replace("Z", "+00:00")
            if iso.endswith("+00:00") or (len(iso) > 19 and (iso[-6] in "+-" or iso.endswith("Z"))):
                parsed = datetime.fromisoformat(iso)
            else:
                local = iso[11:]
                if len(local) == 5:
                    iso = f"{iso[:10]}T{local}:00"
                parsed = datetime.fromisoformat(iso)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError, TypeError):
        return None
    return None


def extract_record_time(payload: dict | None) -> datetime | None:
    data = payload or {}
    for key in DATE_KEYS:
        instant = parse_instant(str(data.get(key) or "") or None)
        if instant:
            return instant
    return None
