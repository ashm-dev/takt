import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from takt.infrastructure.db.schema.tables import (
    BENCHMARK_TABLE,
    LOADED_HASH_TABLE,
    MEASUREMENT_TABLE,
    RUN_METADATA_TABLE,
    SUITE_TABLE,
    WORKER_RUN_TABLE,
)
from takt.infrastructure.db.suite_row_reader import read_suite
from takt.infrastructure.db.suite_row_writer import insert_suite
from tests.infrastructure.db.suite_factory import make_record


def count_rows(connection: sa.Connection, table: sa.Table) -> int:
    return connection.execute(
        sa.select(sa.func.count()).select_from(table),
    ).scalar_one()


def test_insert_then_read_returns_equal_record(engine: sa.Engine) -> None:
    record = make_record()
    with engine.begin() as connection:
        insert_suite(connection, record)

    with engine.connect() as connection:
        assert read_suite(connection, 'a' * 64) == record


def test_read_missing_suite_returns_none(engine: sa.Engine) -> None:
    with engine.connect() as connection:
        assert read_suite(connection, 'b' * 64) is None


def test_insert_preserves_microseconds(engine: sa.Engine) -> None:
    record = make_record()
    with engine.begin() as connection:
        insert_suite(connection, record)

    with engine.connect() as connection:
        stored = read_suite(connection, 'a' * 64)

    assert stored is not None
    result_date = stored.suite.result_date
    assert result_date is not None
    assert result_date == record.suite.result_date
    assert result_date.microsecond == 123456
    assert stored.loaded_at == record.loaded_at


def test_insert_writes_expected_row_counts(engine: sa.Engine) -> None:
    with engine.begin() as connection:
        insert_suite(connection, make_record())

    with engine.connect() as connection:
        counts = {
            table.name: count_rows(connection, table)
            for table in (
                SUITE_TABLE,
                BENCHMARK_TABLE,
                WORKER_RUN_TABLE,
                MEASUREMENT_TABLE,
                RUN_METADATA_TABLE,
                LOADED_HASH_TABLE,
            )
        }

    assert counts == {
        'takt_suite': 1,
        'takt_benchmark': 2,
        'takt_worker_run': 3,
        'takt_measurement': 7,
        'takt_run_metadata': 3,
        'takt_loaded_hash': 1,
    }


def test_insert_stores_null_custom_when_empty(engine: sa.Engine) -> None:
    with engine.begin() as connection:
        insert_suite(connection, make_record())

    with engine.connect() as connection:
        null_positions: list[int] = list(
            connection.execute(
                sa.select(RUN_METADATA_TABLE.c.benchmark_position)
                .where(RUN_METADATA_TABLE.c.custom.is_(sa.null()))
                .order_by(RUN_METADATA_TABLE.c.benchmark_position),
            ).scalars(),
        )

    assert null_positions == [0, 1]


def test_insert_with_null_name_and_date(engine: sa.Engine) -> None:
    with engine.begin() as connection:
        insert_suite(connection, make_record(name=None, result_date=None))

    with engine.connect() as connection:
        stored = read_suite(connection, 'a' * 64)

    assert stored is not None
    assert stored.name is None
    assert stored.suite.result_date is None


def test_insert_duplicate_hash_raises(engine: sa.Engine) -> None:
    record = make_record()
    with engine.connect() as connection:
        insert_suite(connection, record)

        with pytest.raises(IntegrityError):
            insert_suite(connection, record)
