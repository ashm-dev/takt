import pytest
import sqlalchemy as sa
from sqlalchemy.pool import NullPool

from takt.domain.model.target import Target
from takt.infrastructure.db.engine_factory import create_target_engine


def mariadb_engine(url: str) -> sa.Engine:
    return create_target_engine(Target(name=None, url=url, dialect='mariadb'))


def test_mariadb_driver_added() -> None:
    engine = mariadb_engine('mariadb://u:p@h/db')

    assert engine.url.drivername == 'mariadb+pymysql'


@pytest.mark.parametrize(
    ('url', 'charset'),
    [
        ('mariadb://u:p@h/db', 'utf8mb4'),
        ('mariadb+pymysql://u:p@h/db?charset=latin1', 'latin1'),
    ],
)
def test_mariadb_charset_added(url: str, charset: str) -> None:
    assert mariadb_engine(url).url.query['charset'] == charset


def test_sqlite_driver() -> None:
    engine = create_target_engine(
        Target(name=None, url='sqlite:///x.sqlite', dialect='sqlite'),
    )

    assert engine.url.drivername == 'sqlite+pysqlite'


def test_null_pool(sqlite_target: Target) -> None:
    assert isinstance(create_target_engine(sqlite_target).pool, NullPool)


def test_sqlite_foreign_keys_pragma(sqlite_target: Target) -> None:
    engine = create_target_engine(sqlite_target)

    with engine.connect() as connection:
        enabled: int = connection.exec_driver_sql(
            'PRAGMA foreign_keys',
        ).scalar_one()

    assert enabled == 1
