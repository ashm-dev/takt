"""SQLAlchemy engine for one target database."""

import sqlalchemy as sa
from sqlalchemy.engine import make_url
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.pool import ConnectionPoolEntry, NullPool

from takt.domain.model.target import Target
from takt.infrastructure.config.dialect_registry import DIALECTS


def create_target_engine(target: Target) -> sa.Engine:
    """Create an engine without a connection pool for a target.

    :param target: Target database.
    :returns: The engine; no connection is opened yet.
    """
    url = make_url(target.url)
    dialect_info = DIALECTS[target.dialect]
    if '+' not in url.drivername:
        # Without an explicit driver mariadb:// looks for MySQLdb.
        url = url.set(
            drivername=f'{dialect_info.backend}+{dialect_info.allowed_drivers[0]}',
        )
    if target.dialect == 'mariadb' and 'charset' not in url.query:
        url = url.update_query_dict({'charset': 'utf8mb4'})
    engine = sa.create_engine(url, poolclass=NullPool)
    if target.dialect == 'sqlite':
        sa.event.listen(engine, 'connect', _enable_foreign_keys)
    return engine


def _enable_foreign_keys(
    dbapi_connection: DBAPIConnection,
    _record: ConnectionPoolEntry,
) -> None:
    # SQLite does not check foreign keys unless each connection enables it.
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()
