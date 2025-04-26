import random

from datetime import datetime, timedelta, timezone
from time import perf_counter, sleep


def now_utc_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def is_older_than_a_week(dt: datetime) -> bool:
    return dt < datetime.now(tz=timezone.utc) - timedelta(weeks=1)


def time_block(label: str):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            print(f"⏱️ Starting: {label}")
            start = perf_counter()
            result = fn(*args, **kwargs)
            duration = perf_counter() - start
            print(f"✅ Finished {label} in {duration:.2f}s")
            return result

        return wrapper

    return decorator


def polite_sleep(min_delay=1.5, max_delay=4.0):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            sleep(random.uniform(min_delay, max_delay))
            result = fn(*args, **kwargs)
            return result

        return wrapper

    return decorator
