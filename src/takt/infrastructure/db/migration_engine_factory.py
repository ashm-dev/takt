"""SQLAlchemy engine for schema migrations."""

import sqlalchemy as sa
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.pool import ConnectionPoolEntry

from takt.domain.model.target import Target
from takt.infrastructure.db.engine_factory import create_target_engine


def create_migration_engine(target: Target) -> sa.Engine:
    """Create a target engine that runs SQLite DDL inside a transaction.

    :param target: Target database.
    :returns: The engine; no connection is opened yet.
    """
    engine = create_target_engine(target)
    # Not for sessions: a read inside BEGIN makes other SQLite writers fail.
    if target.dialect == 'sqlite':
        sa.event.listen(engine, 'connect', _disable_driver_transactions)
        sa.event.listen(engine, 'begin', _begin_transaction)
    return engine


def _disable_driver_transactions(
    dbapi_connection: DBAPIConnection,
    _record: ConnectionPoolEntry,
) -> None:
    # pysqlite runs DDL outside any transaction, so takt emits BEGIN itself.
    dbapi_connection.isolation_level = None


def _begin_transaction(connection: sa.Connection) -> None:
    connection.exec_driver_sql('BEGIN')
