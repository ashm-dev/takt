"""Execution error built from a database error."""

from sqlalchemy.exc import DBAPIError

from takt.domain.errors.execution_error import ExecutionError


def database_error(message: str, error: Exception) -> ExecutionError:
    """Build a one-line error with the driver message as the reason.

    :param message: What failed, including the database label.
    :param error: Error raised by SQLAlchemy or the database driver.
    :returns: Error with the text ``<message>: <reason>``.
    """
    if isinstance(error, DBAPIError) and error.orig is not None:
        reason = str(error.orig)
    else:
        reason = str(error)
    return ExecutionError(f'{message}: {reason}')
