from contextlib import closing
from dataclasses import replace

import pytest
import sqlalchemy as sa

from takt.domain.errors.execution_error import ExecutionError
from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.model.target import Target
from takt.infrastructure.db.alembic_schema_migrator import AlembicSchemaMigrator
from takt.infrastructure.db.migration_engine_factory import (
    create_migration_engine,
)
from takt.infrastructure.db.schema.tables import (
    BENCHMARK_TABLE,
    LOADED_HASH_TABLE,
)
from takt.infrastructure.db.sqlalchemy_target_connector import (
    SqlAlchemyTargetConnector,
)
from takt.infrastructure.db.sqlalchemy_target_session import (
    SqlAlchemyTargetSession,
)
from tests.infrastructure.db.suite_factory import DEFAULT_HASH, make_record

MISSING_HASH = 'd' * 64
"""Suite hash that is never stored in the test database."""


def loaded_name(target: Target) -> tuple[bool, str | None]:
    with closing(SqlAlchemyTargetConnector().open(target)) as session:
        return session.loaded_name(DEFAULT_HASH)


class RecordingDispose:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1


def test_loaded_name_for_missing_hash(target: Target) -> None:
    assert loaded_name(target) == (False, None)


def test_loaded_name_after_commit(target: Target) -> None:
    session = SqlAlchemyTargetConnector().open(target)
    session.insert(make_record(name='x'))
    session.commit()
    session.close()

    assert loaded_name(target) == (True, 'x')


def test_loaded_name_without_suite_row(
    target: Target,
    engine: sa.Engine,
) -> None:
    with engine.begin() as connection:
        connection.execute(LOADED_HASH_TABLE.insert(), {'hash': DEFAULT_HASH})

    assert loaded_name(target) == (True, None)


def test_rollback_discards_insert(target: Target) -> None:
    session = SqlAlchemyTargetConnector().open(target)
    session.insert(make_record())
    session.rollback()
    session.close()

    assert loaded_name(target) == (False, None)


def test_get_missing_raises_operand_not_found(target: Target) -> None:
    with (
        closing(SqlAlchemyTargetConnector().open(target)) as session,
        pytest.raises(OperandNotFoundError) as caught,
    ):
        session.get(MISSING_HASH)

    assert str(caught.value) == f'suite {MISSING_HASH} not found'


def test_rollback_after_commit_is_noop(target: Target) -> None:
    session = SqlAlchemyTargetConnector().open(target)
    session.commit()
    session.rollback()
    session.close()


def test_close_twice_is_safe(target: Target) -> None:
    session = SqlAlchemyTargetConnector().open(target)
    session.close()
    session.close()


def test_open_invalid_url_disposes_engine() -> None:
    unreachable = Target(
        name=None,
        url='mariadb+pymysql://u:p@127.0.0.1:1/db',
        dialect='mariadb',
    )

    with pytest.raises(ExecutionError) as connect_error:
        SqlAlchemyTargetConnector().open(unreachable)

    assert str(connect_error.value).startswith(
        'cannot connect to database mariadb+pymysql://u:***@127.0.0.1:1/db: ',
    )
    assert ':p@' not in str(connect_error.value)


def test_open_invalid_url_parameter_raises_execution_error(
    sqlite_target: Target,
) -> None:
    bad_timeout = replace(sqlite_target, url=f'{sqlite_target.url}?timeout=abc')

    with pytest.raises(ExecutionError) as connect_error:
        SqlAlchemyTargetConnector().open(bad_timeout)

    assert str(connect_error.value) == (
        f'cannot connect to database {bad_timeout.display()}: '
        "could not convert string to float: 'abc'"
    )


def test_open_driver_error_disposes_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispose = RecordingDispose()
    monkeypatch.setattr(sa.Engine, 'dispose', dispose)
    unknown_option = Target(
        name=None,
        url='mariadb+pymysql://u:p@127.0.0.1:1/db?unknown=1',
        dialect='mariadb',
    )

    with pytest.raises(ExecutionError) as connect_error:
        SqlAlchemyTargetConnector().open(unknown_option)

    assert str(connect_error.value).startswith(
        'cannot connect to database '
        'mariadb+pymysql://u:***@127.0.0.1:1/db?unknown=1: ',
    )
    assert str(connect_error.value).endswith(
        "unexpected keyword argument 'unknown'",
    )
    assert dispose.calls == 1


@pytest.mark.parametrize(
    ('method', 'arguments'),
    [
        ('loaded_name', (MISSING_HASH,)),
        ('get', (MISSING_HASH,)),
        ('find_by_name', ('x',)),
        ('find_by_hash_prefix', ('d', None)),
    ],
)
def test_read_without_schema_raises_execution_error(
    sqlite_target: Target,
    method: str,
    arguments: tuple[str | None, ...],
) -> None:
    with (
        closing(SqlAlchemyTargetConnector().open(sqlite_target)) as session,
        pytest.raises(ExecutionError) as read_error,
    ):
        getattr(session, method)(*arguments)

    engine_url = sqlite_target.url.replace('sqlite:', 'sqlite+pysqlite:', 1)
    assert str(read_error.value).startswith(
        f'cannot read from database {engine_url}: no such table: ',
    )


@pytest.mark.parametrize(
    ('method', 'arguments'),
    [
        ('insert', (make_record(),)),
        ('delete', (MISSING_HASH,)),
    ],
)
def test_write_without_schema_raises_execution_error(
    sqlite_target: Target,
    method: str,
    arguments: tuple[object, ...],
) -> None:
    with (
        closing(SqlAlchemyTargetConnector().open(sqlite_target)) as session,
        pytest.raises(ExecutionError) as write_error,
    ):
        getattr(session, method)(*arguments)

    engine_url = sqlite_target.url.replace('sqlite:', 'sqlite+pysqlite:', 1)
    assert str(write_error.value).startswith(
        f'cannot write to database {engine_url}: no such table: ',
    )


def session_with_orphan_benchmark(target: Target) -> SqlAlchemyTargetSession:
    engine = create_migration_engine(target)
    connection = engine.connect()
    transaction = connection.begin()
    connection.exec_driver_sql('PRAGMA defer_foreign_keys=ON')
    connection.execute(
        BENCHMARK_TABLE.insert(),
        {'suite_hash': MISSING_HASH, 'benchmark_position': 0, 'name': 'x'},
    )
    return SqlAlchemyTargetSession(
        engine=engine,
        connection=connection,
        transaction=transaction,
    )


def test_commit_failure_raises_execution_error(sqlite_target: Target) -> None:
    AlembicSchemaMigrator().upgrade(sqlite_target)
    session = session_with_orphan_benchmark(sqlite_target)

    with closing(session), pytest.raises(ExecutionError) as commit_error:
        session.commit()

    engine_url = sqlite_target.url.replace('sqlite:', 'sqlite+pysqlite:', 1)
    assert str(commit_error.value) == (
        f'cannot commit to database {engine_url}: FOREIGN KEY constraint failed'
    )


def test_sqlite_writers_do_not_block_each_other(sqlite_target: Target) -> None:
    AlembicSchemaMigrator().upgrade(sqlite_target)
    connector = SqlAlchemyTargetConnector()
    first = make_record(suite_hash='b' * 64)
    second = make_record(suite_hash='c' * 64)

    with (
        closing(connector.open(sqlite_target)) as first_session,
        closing(connector.open(sqlite_target)) as second_session,
    ):
        first_session.loaded_name(first.suite.hash)
        first_session.insert(first)
        second_session.loaded_name(second.suite.hash)
        first_session.commit()
        second_session.insert(second)
        second_session.commit()
