from datetime import datetime, timedelta, timezone
from scraper.utils.time_util import now_utc_iso, is_older_than_a_week, time_block, polite_sleep


def test_now_utc_iso_has_timezone():
    ts = now_utc_iso()
    dt = datetime.fromisoformat(ts)
    assert dt.tzinfo is not None


def test_is_older_than_a_week():
    old = datetime.now(tz=timezone.utc) - timedelta(days=8)
    recent = datetime.now(tz=timezone.utc) - timedelta(days=6)
    assert is_older_than_a_week(old)
    assert not is_older_than_a_week(recent)


def test_time_block_decorator(capsys):
    @time_block("test")
    def add(a, b):
        return a + b

    result = add(1, 2)
    out = capsys.readouterr().out
    assert result == 3
    assert "Starting: test" in out
    assert "Finished test" in out


def test_polite_sleep_decorator():
    calls = []

    @polite_sleep(min_delay=0, max_delay=0)
    def foo(x):
        calls.append(x)
        return x

    assert foo(42) == 42
    assert calls == [42]
