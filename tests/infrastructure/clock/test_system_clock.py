from datetime import UTC, datetime

from takt.infrastructure.clock.system_clock import SystemClock


def test_now_is_utc() -> None:
    before = datetime.now(UTC)
    now = SystemClock().now()
    after = datetime.now(UTC)
    assert now.tzinfo is UTC
    assert before <= now <= after
