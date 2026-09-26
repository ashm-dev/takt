import pytest
import sqlalchemy as sa

from takt.infrastructure.db.database_error import database_error


@pytest.mark.parametrize(
    ('error', 'reason'),
    [
        (
            sa.exc.StatementError(
                '(builtins.TypeError) boom',
                'INSERT INTO t VALUES (?)',
                (1,),
                TypeError('boom'),
            ),
            'boom',
        ),
        (
            sa.exc.PendingRollbackError('Cannot reconnect', code='8s2b'),
            'Cannot reconnect',
        ),
        (
            sa.exc.ArgumentError('Invalid SQLite URL\nValid forms are:'),
            'Invalid SQLite URL',
        ),
        (ValueError('bad value'), 'bad value'),
    ],
)
def test_reason_is_one_line(error: Exception, reason: str) -> None:
    assert str(database_error('cannot connect to database x', error)) == (
        f'cannot connect to database x: {reason}'
    )
