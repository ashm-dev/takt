from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from takt.domain.errors.execution_error import ExecutionError
from takt.domain.model.target import Target
from takt.infrastructure.db.alembic_schema_migrator import AlembicSchemaMigrator
from takt.infrastructure.db.sqlalchemy_read_connector import (
    SqlAlchemyReadConnector,
)
from tests.domain.exact_pattern import exact_pattern

READER = SqlAlchemyReadConnector()


def database_path(target: Target) -> Path:
    return Path(target.url.removeprefix('sqlite:///'))


def test_reader_does_not_create_missing_file(sqlite_target: Target) -> None:
    path = database_path(sqlite_target)
    message = (
        f'cannot connect to database {sqlite_target.url}: '
        f'database file not found: {path}'
    )

    with pytest.raises(ExecutionError, match=exact_pattern(message)):
        READER.open(sqlite_target)

    assert not path.exists()


def test_reader_does_not_create_missing_uri_file(
    sqlite_target: Target,
) -> None:
    path = database_path(sqlite_target)
    uri = replace(sqlite_target, url=f'sqlite:///file:{path}?uri=true')
    message = (
        f'cannot connect to database {uri.display()}: '
        f'database file not found: {path}'
    )

    with pytest.raises(ExecutionError, match=exact_pattern(message)):
        READER.open(uri)

    assert not path.exists()


def test_reader_rejects_database_without_takt_tables(
    sqlite_target: Target,
) -> None:
    database_path(sqlite_target).touch()
    named = replace(sqlite_target, name='local')

    with pytest.raises(
        ExecutionError,
        match=exact_pattern('no takt results in database local'),
    ):
        READER.open(named)


def test_reader_opens_migrated_database(sqlite_target: Target) -> None:
    AlembicSchemaMigrator().upgrade(sqlite_target)

    with closing(READER.open(sqlite_target)) as session:
        assert session.has_schema()
