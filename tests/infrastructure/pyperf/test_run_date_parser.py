from datetime import datetime

import pytest

from takt.infrastructure.pyperf.run_date_parser import parse_run_date


@pytest.mark.usefixtures('local_time_plus_three_hours')
def test_aware_date_becomes_local_naive() -> None:
    parsed = parse_run_date('2026-09-25T12:00:00+02:00')

    assert parsed == datetime.fromisoformat('2026-09-25 13:00:00')


@pytest.mark.parametrize(
    'date', ['0001-01-01T00:00:00+05:00', '9999-12-31T23:59:59-05:00']
)
def test_out_of_range_aware_date_is_skipped(date: str) -> None:
    assert parse_run_date(date) is None
