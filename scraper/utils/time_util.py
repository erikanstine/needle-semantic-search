from datetime import datetime, timezone
from time import perf_counter


def now_utc_iso():
    return datetime.now(tz=timezone.utc).isoformat()


def time_block(label: str):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            print(f"⏱️ Starting: {label}")
            start = perf_counter()
            result = fn(*args, **kwargs)
            duration = perf_counter() - start
            print(f"✅ Finished {label} in {duration:.2f}s")
            # return result, duration
            return result

        return wrapper

    return decorator
