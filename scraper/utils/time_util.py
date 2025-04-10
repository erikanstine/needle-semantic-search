from datetime import datetime, timezone


def now_utc_iso():
    return datetime.now(tz=timezone.utc).isoformat()
