from contextlib import closing

import pytest

from takt.domain.errors.execution_error import ExecutionError
from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.model.target import Target
from takt.infrastructure.db.sqlalchemy_target_connector import (
    SqlAlchemyTargetConnector,
)
from tests.infrastructure.db.suite_factory import DEFAULT_HASH, make_record

MISSING_HASH = 'd' * 64


def loaded_name(target: Target) -> tuple[bool, str | None]:
    with closing(SqlAlchemyTargetConnector().open(target)) as session:
        return session.loaded_name(DEFAULT_HASH)


def test_loaded_name_for_missing_hash(target: Target) -> None:
    assert loaded_name(target) == (False, None)


def test_loaded_name_after_commit(target: Target) -> None:
    session = SqlAlchemyTargetConnector().open(target)
    session.insert(make_record(name='x'))
    session.commit()
    session.close()

    assert loaded_name(target) == (True, 'x')


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
    target = Target(
        name=None,
        url='mariadb+pymysql://u:p@127.0.0.1:1/db',
        dialect='mariadb',
    )

    with pytest.raises(ExecutionError) as connect_error:
        SqlAlchemyTargetConnector().open(target)

    assert str(connect_error.value).startswith(
        'cannot connect to database mariadb+pymysql://u:***@127.0.0.1:1/db: ',
    )
    assert ':p@' not in str(connect_error.value)


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
