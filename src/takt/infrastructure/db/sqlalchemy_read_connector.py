"""Target connector for reads, which never creates a database."""

import contextlib

from takt.domain.errors.execution_error import ExecutionError
from takt.domain.model.target import Target
from takt.infrastructure.db.database_file import require_database_file
from takt.infrastructure.db.sqlalchemy_target_connector import (
    SqlAlchemyTargetConnector,
)
from takt.infrastructure.db.sqlalchemy_target_session import (
    SqlAlchemyTargetSession,
)


class SqlAlchemyReadConnector:
    """Open sessions only to databases that already have takt results."""

    def open(self, target: Target) -> SqlAlchemyTargetSession:
        """Connect to the target and start a transaction.

        :param target: Target database.
        :returns: Session with a started transaction.
        :raises ExecutionError: If the database cannot be reached, or its
            SQLite file or its takt tables are missing.
        """
        require_database_file(target)
        session = SqlAlchemyTargetConnector().open(target)
        with contextlib.ExitStack() as on_failure:
            on_failure.callback(session.close)
            if not session.has_schema():
                msg = f'no takt results in database {target.display()}'
                raise ExecutionError(msg)
            on_failure.pop_all()
        return session
