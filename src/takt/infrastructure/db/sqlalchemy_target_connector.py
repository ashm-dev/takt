"""Target connector backed by SQLAlchemy."""

import contextlib

from sqlalchemy.engine import Engine

from takt.domain.model.target import Target
from takt.infrastructure.db.database_error import database_error
from takt.infrastructure.db.engine_factory import create_target_engine
from takt.infrastructure.db.sqlalchemy_target_session import (
    SqlAlchemyTargetSession,
)


class SqlAlchemyTargetConnector:
    """Open sessions to target databases."""

    def open(self, target: Target) -> SqlAlchemyTargetSession:
        """Connect to the target and start a transaction.

        The schema is neither migrated nor checked.

        :param target: Target database.
        :returns: Session with a started transaction.
        :raises ExecutionError: If the database cannot be reached.
        """
        try:
            return _start_session(create_target_engine(target))
        except Exception as error:
            message = f'cannot connect to database {target.display()}'
            raise database_error(message, error) from error


def _start_session(engine: Engine) -> SqlAlchemyTargetSession:
    with contextlib.ExitStack() as on_failure:
        on_failure.callback(engine.dispose)
        connection = engine.connect()
        session = SqlAlchemyTargetSession(
            engine=engine,
            connection=connection,
            transaction=connection.begin(),
        )
        on_failure.pop_all()
    return session
