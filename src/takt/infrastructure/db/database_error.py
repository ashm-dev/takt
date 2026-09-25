"""Execution error built from a SQLAlchemy error."""

from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from takt.domain.errors.execution_error import ExecutionError


def database_error(message: str, error: SQLAlchemyError) -> ExecutionError:
    """Build a one-line error with the driver message as the reason.

    :param message: What failed, including the database label.
    :param error: Error raised by SQLAlchemy.
    :returns: Error with the text ``<message>: <reason>``.
    """
    if isinstance(error, DBAPIError) and error.orig is not None:
        reason = str(error.orig)
    else:
        reason = str(error)
    return ExecutionError(f'{message}: {reason}')
