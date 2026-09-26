"""Check that the file of a SQLite target exists."""

from pathlib import Path

from sqlalchemy.engine import make_url

from takt.domain.errors.execution_error import ExecutionError
from takt.domain.model.target import Target
from takt.infrastructure.config.sqlite_file_name import sqlite_file_name


def require_database_file(target: Target) -> None:
    """Raise if a SQLite target has no database file yet.

    SQLite creates a missing file on connect, so a read would leave an empty
    file behind a typo in the path.

    :param target: Target database.
    :raises ExecutionError: If the SQLite file does not exist.
    """
    if target.dialect != 'sqlite':
        return
    path = sqlite_file_name(make_url(target.url))
    if path and not Path(path).is_file():
        msg = (
            f'cannot connect to database {target.display()}: '
            f'database file not found: {path}'
        )
        raise ExecutionError(msg)
