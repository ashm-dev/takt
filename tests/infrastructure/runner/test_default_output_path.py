from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from takt.infrastructure.runner.default_output_path import default_output_path

PLUS_THREE = timezone(timedelta(hours=3))
EXPECTED = Path('/work/takt-20260925T134601Z.json')


def test_utc_name() -> None:
    now = datetime(2026, 9, 25, 13, 46, 1, tzinfo=UTC)
    assert default_output_path(now, Path('/work')) == EXPECTED


def test_converts_to_utc() -> None:
    now = datetime(2026, 9, 25, 16, 46, 1, tzinfo=PLUS_THREE)
    assert default_output_path(now, Path('/work')) == EXPECTED
