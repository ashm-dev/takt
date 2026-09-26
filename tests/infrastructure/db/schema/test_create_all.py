from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from takt.domain.model.target import Target
from takt.infrastructure.db.engine_factory import create_target_engine
from takt.infrastructure.db.schema.tables import (
    BENCHMARK_TABLE,
    METADATA,
    RUN_METADATA_TABLE,
    SUITE_TABLE,
    WORKER_RUN_TABLE,
)
from tests.infrastructure.db.schema.expected_schema import (
    FOREIGN_KEYS,
    INDEX_NAMES,
    PRIMARY_KEYS,
    TABLE_NAMES,
    ForeignKey,
)

SUITE_HASH = 'a' * 64


def create_schema(target: Target) -> sa.Engine:
    engine = create_target_engine(target)
    METADATA.create_all(engine)
    return engine


def foreign_keys(
    inspector: sa.Inspector,
    table_name: str,
) -> tuple[ForeignKey, ...]:
    return tuple(
        (
            tuple(foreign_key['constrained_columns']),
            foreign_key['referred_table'],
            tuple(foreign_key['referred_columns']),
        )
        for foreign_key in inspector.get_foreign_keys(table_name)
    )


def assert_keys(inspector: sa.Inspector) -> None:
    for table_name, primary_key in PRIMARY_KEYS:
        constraint = inspector.get_pk_constraint(table_name)
        assert tuple(constraint['constrained_columns']) == primary_key
    reflected = tuple(
        (name, foreign_key)
        for name, _ in PRIMARY_KEYS
        for foreign_key in foreign_keys(inspector, name)
    )
    assert reflected == FOREIGN_KEYS


def assert_schema(engine: sa.Engine) -> None:
    inspector = sa.inspect(engine)
    assert set(inspector.get_table_names()) == TABLE_NAMES
    assert_keys(inspector)
    indexes = inspector.get_indexes('takt_suite')
    assert {index['name'] for index in indexes} == INDEX_NAMES


def insert_orphan_benchmark(engine: sa.Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            BENCHMARK_TABLE.insert().values(
                suite_hash=SUITE_HASH,
                benchmark_position=0,
                name='bench',
            ),
        )


def insert_parent_rows(connection: sa.Connection) -> None:
    connection.execute(
        SUITE_TABLE.insert().values(
            hash=SUITE_HASH,
            name=None,
            format_version='1.0',
            source='import',
            result_date=None,
            loaded_at=datetime.now(UTC).replace(tzinfo=None),
        ),
    )
    connection.execute(
        BENCHMARK_TABLE.insert().values(
            suite_hash=SUITE_HASH,
            benchmark_position=0,
            name='bench',
        ),
    )
    connection.execute(
        WORKER_RUN_TABLE.insert().values(
            suite_hash=SUITE_HASH,
            benchmark_position=0,
            run_position=0,
        ),
    )


def test_create_all_sqlite(sqlite_target: Target) -> None:
    assert_schema(create_schema(sqlite_target))


@pytest.mark.mariadb
def test_create_all_mariadb(mariadb_target: Target) -> None:
    engine = create_schema(mariadb_target)

    assert_schema(engine)
    with engine.connect() as connection:
        row = connection.exec_driver_sql('SHOW CREATE TABLE takt_suite').one()
    assert 'DATETIME(6)' in row[1].upper()
    assert 'ENGINE=InnoDB' in row[1]


def test_sqlite_enforces_foreign_keys(sqlite_target: Target) -> None:
    engine = create_schema(sqlite_target)

    with pytest.raises(sa.exc.IntegrityError):
        insert_orphan_benchmark(engine)


@pytest.mark.mariadb
def test_mariadb_enforces_foreign_keys(mariadb_target: Target) -> None:
    engine = create_schema(mariadb_target)

    with pytest.raises(sa.exc.IntegrityError):
        insert_orphan_benchmark(engine)


@pytest.mark.mariadb
def test_mariadb_long_metadata_row(mariadb_target: Target) -> None:
    engine = create_schema(mariadb_target)
    long_texts = {
        column.name: 'x' * 500
        for column in RUN_METADATA_TABLE.columns
        if isinstance(column.type, sa.Text)
    }

    with engine.begin() as connection:
        insert_parent_rows(connection)
        connection.execute(
            RUN_METADATA_TABLE.insert().values(
                suite_hash=SUITE_HASH,
                benchmark_position=0,
                run_position=0,
                **long_texts,
            ),
        )

    with engine.connect() as connection:
        count = connection.execute(
            sa.select(sa.func.count()).select_from(RUN_METADATA_TABLE),
        ).scalar_one()
    assert count == 1
