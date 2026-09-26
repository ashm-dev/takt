from importlib import util

import pytest

from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.missing_driver_error import MissingDriverError
from takt.domain.errors.unsupported_dialect_error import (
    UnsupportedDialectError,
)
from takt.infrastructure.config.dialect_registry import (
    DIALECTS,
    dialect_for_url,
)

REAL_FIND_SPEC = util.find_spec


def find_spec_without_pymysql(name: str) -> object:
    if name == 'pymysql':
        return None
    return REAL_FIND_SPEC(name)


@pytest.mark.parametrize(
    'url',
    ['sqlite:///b.sqlite', 'sqlite+pysqlite:///b.sqlite'],
)
def test_sqlite(url: str) -> None:
    assert dialect_for_url(url) == DIALECTS['sqlite']


@pytest.mark.parametrize(
    'url',
    ['mariadb://u:p@h/db', 'mariadb+pymysql://u:p@h/db'],
)
def test_mariadb(url: str) -> None:
    assert dialect_for_url(url) == DIALECTS['mariadb']


@pytest.mark.parametrize(
    ('backend', 'extra'),
    [('sqlite', None), ('mariadb', 'mariadb')],
)
def test_extra(backend: str, extra: str | None) -> None:
    assert DIALECTS[backend].extra == extra


@pytest.mark.parametrize(
    ('url', 'backend'),
    [
        ('mysql+pymysql://u@h/db', 'mysql'),
        ('postgresql://u@h/db', 'postgresql'),
        ('duckdb:///x.db', 'duckdb'),
        ('clickhouse://u@h/db', 'clickhouse'),
    ],
)
def test_unsupported_backend(url: str, backend: str) -> None:
    with pytest.raises(UnsupportedDialectError) as error:
        dialect_for_url(url)

    assert str(error.value) == (
        f'unsupported database {backend!r}; '
        'supported in this version: mariadb, sqlite'
    )


@pytest.mark.parametrize(
    ('url', 'message'),
    [
        (
            'mariadb+mysqldb://u@h/db',
            "unsupported driver 'mysqldb' for mariadb; supported: pymysql",
        ),
        (
            'sqlite+aiosqlite:///x',
            "unsupported driver 'aiosqlite' for sqlite; supported: pysqlite",
        ),
    ],
)
def test_unsupported_driver(url: str, message: str) -> None:
    with pytest.raises(UnsupportedDialectError) as error:
        dialect_for_url(url)

    assert str(error.value) == message


def test_missing_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(util, 'find_spec', find_spec_without_pymysql)

    with pytest.raises(MissingDriverError) as error:
        dialect_for_url('mariadb://u:p@h/db')

    assert str(error.value) == (
        "database driver 'pymysql' for mariadb is not installed; "
        "run: pip install 'takt[mariadb]'"
    )
    assert error.value.exit_code == 2


@pytest.mark.parametrize(
    'url',
    [
        'not a url',
        'mariadb+pymysql://u:p@h:abc/db',
        'mariadb+pymysql://u:p@h:/db',
    ],
)
def test_invalid_url(url: str) -> None:
    with pytest.raises(ConfigurationError) as error:
        dialect_for_url(url)

    assert str(error.value) == f'invalid database URL: {url!r}'
