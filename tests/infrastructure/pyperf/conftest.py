import time
from collections.abc import Iterator

import pytest


@pytest.fixture
def local_time_plus_three_hours(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    # POSIX TZ strings invert the sign, so this zone is UTC+3.
    monkeypatch.setenv('TZ', 'TKT-3')
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()
