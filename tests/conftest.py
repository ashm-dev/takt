import contextlib
import gc
import uuid
import warnings
from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import make_url
from testcontainers.community.mysql import MySqlContainer

from takt.domain.model.target import Target

MARIADB_IMAGE = 'mariadb:11.4'
ACCOUNT = 'takt'
ROOT = 'root'


@pytest.fixture
def sqlite_target(tmp_path: Path) -> Target:
    database_path = tmp_path / 'takt.sqlite'
    return Target(
        name=None,
        url=f'sqlite:///{database_path}',
        dialect='sqlite',
    )


@pytest.fixture(scope='session')
def mariadb_container() -> Iterator[MySqlContainer]:
    container = None
    with contextlib.suppress(Exception):
        container = MySqlContainer(
            MARIADB_IMAGE,
            username=ACCOUNT,
            password=ACCOUNT,
            root_password=ROOT,
            dbname='takt',
            dialect='pymysql',
        ).start()
    if container is None:
        # The Docker client leaks its socket when the daemon is missing.
        with warnings.catch_warnings(action='ignore', category=ResourceWarning):
            gc.collect()
        pytest.skip('Docker is not available')
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def mariadb_target(mariadb_container: MySqlContainer) -> Iterator[Target]:
    user_url = make_url(
        mariadb_container.get_connection_url().replace(
            'mysql+pymysql://',
            'mariadb+pymysql://',
            1,
        ),
    )
    suffix = uuid.uuid4().hex[:8]
    database = f'takt_test_{suffix}'
    root_engine = sa.create_engine(
        user_url.set(username=ROOT, password=ROOT, database=None),
        poolclass=sa.pool.NullPool,
    )
    with root_engine.begin() as connection:
        connection.execute(sa.text(f'CREATE DATABASE {database}'))
        connection.execute(
            sa.text(f"GRANT ALL ON {database}.* TO '{ACCOUNT}'@'%'"),
        )
    try:
        yield Target(
            name=None,
            url=user_url.set(database=database).render_as_string(
                hide_password=False,
            ),
            dialect='mariadb',
        )
    finally:
        with root_engine.begin() as connection:
            connection.execute(sa.text(f'DROP DATABASE {database}'))
        root_engine.dispose()
