"""Execution error built from a database error."""

from sqlalchemy.exc import SQLAlchemyError, StatementError

from takt.domain.errors.execution_error import ExecutionError


def database_error(message: str, error: Exception) -> ExecutionError:
    """Build a one-line error with the driver message as the reason.

    :param message: What failed, including the database label.
    :param error: Error raised by SQLAlchemy or the database driver.
    :returns: Error with the text ``<message>: <first line of the reason>``.
    """
    reason = _reason(error).partition('\n')[0]
    return ExecutionError(f'{message}: {reason}')


def _reason(error: Exception) -> str:
    if isinstance(error, StatementError) and error.orig is not None:
        return str(error.orig)
    if isinstance(error, SQLAlchemyError):
        # SQLAlchemy's own __str__ appends the SQL and a documentation link.
        return Exception.__str__(error)
    return str(error)
