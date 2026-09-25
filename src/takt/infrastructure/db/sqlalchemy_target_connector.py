"""Target connector backed by SQLAlchemy."""

from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

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
        engine = create_target_engine(target)
        try:
            return _start_session(engine)
        except SQLAlchemyError as error:
            engine.dispose()
            message = f'cannot connect to database {target.display()}'
            raise database_error(message, error) from error
        except BaseException:
            engine.dispose()
            raise


def _start_session(engine: Engine) -> SqlAlchemyTargetSession:
    connection = engine.connect()
    return SqlAlchemyTargetSession(
        engine=engine,
        connection=connection,
        transaction=connection.begin(),
    )
