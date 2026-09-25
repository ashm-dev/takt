from contextlib import closing

import pytest
from sqlalchemy.exc import OperationalError

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

    with pytest.raises(OperationalError):
        SqlAlchemyTargetConnector().open(target)
