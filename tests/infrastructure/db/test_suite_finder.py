from collections.abc import Iterator
from datetime import datetime

import pytest
import sqlalchemy as sa

from takt.infrastructure.db.suite_finder import (
    find_by_hash_prefix,
    find_by_name,
)
from takt.infrastructure.db.suite_row_writer import insert_suite
from tests.infrastructure.db.suite_factory import make_record

FIRST_DAY = datetime.fromisoformat('2026-01-01')
"""Earlier result date."""

SECOND_DAY = datetime.fromisoformat('2026-01-02')
"""Later result date."""

ONE = '1' * 64
"""Hash of the ``default`` suite dated ``SECOND_DAY``."""

TWO = '2' * 64
"""Hash of the ``default`` suite dated ``FIRST_DAY``."""

THREE = '3' * 64
"""Hash of the ``default`` suite without a result date."""

FOUR = '4' * 64
"""Hash of the ``other`` suite dated ``FIRST_DAY``."""

FIVE = '5' * 64
"""Hash of a suite that one test adds to tie with ``FOUR``."""

STORED = (
    (ONE, 'default', SECOND_DAY),
    (TWO, 'default', FIRST_DAY),
    (THREE, 'default', None),
    (FOUR, 'other', FIRST_DAY),
)
"""Hash, name and result date of the suites that the fixture inserts."""


def insert(
    connection: sa.Connection,
    suite_hash: str,
    name: str,
    result_date: datetime | None,
) -> None:
    insert_suite(
        connection,
        make_record(suite_hash=suite_hash, name=name, result_date=result_date),
    )


@pytest.fixture
def connection(engine: sa.Engine) -> Iterator[sa.Connection]:
    with engine.begin() as setup:
        for suite_hash, name, result_date in STORED:
            insert(setup, suite_hash, name, result_date)
    with engine.connect() as opened:
        yield opened


def test_find_by_name_orders_by_date_then_nulls(
    connection: sa.Connection,
) -> None:
    found = find_by_name(connection, 'default')

    assert [summary.hash for summary in found] == [TWO, ONE, THREE]


def test_find_by_name_is_exact(connection: sa.Connection) -> None:
    assert find_by_name(connection, 'Default') == ()
    assert find_by_name(connection, 'def') == ()


def test_find_by_hash_prefix_without_name(connection: sa.Connection) -> None:
    found = find_by_hash_prefix(connection, '222222', None)

    assert [summary.hash for summary in found] == [TWO]


def test_find_by_hash_prefix_with_name(connection: sa.Connection) -> None:
    assert find_by_hash_prefix(connection, '444444', 'default') == ()
    found = find_by_hash_prefix(connection, '444444', 'other')

    assert [summary.hash for summary in found] == [FOUR]


def test_find_by_hash_prefix_ties_break_by_hash(
    connection: sa.Connection,
) -> None:
    insert(connection, FIVE, 'other', FIRST_DAY)

    found = find_by_name(connection, 'other')

    assert [summary.hash for summary in found] == [FOUR, FIVE]


def test_find_returns_summary_fields(connection: sa.Connection) -> None:
    found = find_by_hash_prefix(connection, '222222', None)

    assert len(found) == 1
    summary = found[0]
    assert summary.name == 'default'
    assert summary.result_date == FIRST_DAY
