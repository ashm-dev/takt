import typing

import pytest
import sqlalchemy as sa
from sqlalchemy.schema import CreateTable

from takt.domain.model.metadata_key_types import METADATA_KEY_TYPES
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.target import Target
from takt.infrastructure.db.engine_factory import create_target_engine
from takt.infrastructure.db.schema.tables import (
    BENCHMARK_TABLE,
    LOADED_HASH_TABLE,
    MEASUREMENT_TABLE,
    METADATA,
    RUN_METADATA_TABLE,
    SUITE_TABLE,
)
from tests.infrastructure.db.schema.expected_schema import (
    FOREIGN_KEYS,
    INDEX_NAMES,
    PRIMARY_KEYS,
    RUN_KEY,
    TABLE_NAMES,
    ForeignKey,
)

EXPECTED_COLUMN_TYPES = (
    (int | None, sa.BigInteger),
    (float | None, sa.Double),
    (str | None, sa.Text),
    (tuple[str, ...] | None, sa.JSON),
)


def test_table_names() -> None:
    assert set(METADATA.tables) == TABLE_NAMES


@pytest.mark.parametrize(('table_name', 'expected'), PRIMARY_KEYS)
def test_primary_keys(table_name: str, expected: tuple[str, ...]) -> None:
    table = METADATA.tables[table_name]

    names = tuple(column.name for column in table.primary_key.columns)

    assert names == expected


def test_run_metadata_columns() -> None:
    names = tuple(column.name for column in RUN_METADATA_TABLE.columns)

    assert names == (*RUN_KEY, *METADATA_KEY_TYPES, 'custom')


@pytest.mark.parametrize('key', tuple(METADATA_KEY_TYPES))
def test_metadata_column_types_match_run_metadata(key: str) -> None:
    hint = typing.get_type_hints(RunMetadata)[key]
    column_type = RUN_METADATA_TABLE.c[key].type

    expected = [
        type_class
        for annotation, type_class in EXPECTED_COLUMN_TYPES
        if annotation == hint
    ]

    assert len(expected) == 1
    assert isinstance(column_type, expected[0])


def test_nullable() -> None:
    assert SUITE_TABLE.c.name.nullable
    assert SUITE_TABLE.c.result_date.nullable
    assert not SUITE_TABLE.c.loaded_at.nullable
    assert not BENCHMARK_TABLE.c.name.nullable
    assert not MEASUREMENT_TABLE.c.value.nullable
    assert all(
        RUN_METADATA_TABLE.c[key].nullable
        for key in (*METADATA_KEY_TYPES, 'custom')
    )


@pytest.mark.parametrize(('table_name', 'expected'), FOREIGN_KEYS)
def test_foreign_keys(table_name: str, expected: ForeignKey) -> None:
    constraints = list(METADATA.tables[table_name].foreign_key_constraints)

    assert len(constraints) == 1
    constraint = constraints[0]
    referred = tuple(element.column.name for element in constraint.elements)
    assert (
        tuple(constraint.column_keys),
        constraint.referred_table.name,
        referred,
    ) == expected


@pytest.mark.parametrize('table', [SUITE_TABLE, LOADED_HASH_TABLE])
def test_tables_without_foreign_keys(table: sa.Table) -> None:
    assert not table.foreign_key_constraints


def test_index_names() -> None:
    assert {index.name for index in SUITE_TABLE.indexes} == INDEX_NAMES


def test_mariadb_ddl() -> None:
    engine = create_target_engine(
        Target(name=None, url='mariadb+pymysql://u:p@h/db', dialect='mariadb'),
    )

    ddl = str(CreateTable(SUITE_TABLE).compile(dialect=engine.dialect))

    assert 'result_date DATETIME(6)' in ddl
    assert 'ENGINE=InnoDB' in ddl
    assert 'CHARSET=utf8mb4' in ddl
