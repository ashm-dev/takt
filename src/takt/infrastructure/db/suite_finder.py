"""Search of stored suites by name or hash prefix."""

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from takt.domain.model.suite_summary import SuiteSummary
from takt.infrastructure.db.schema.tables import SUITE_TABLE


def find_by_name(connection: Connection, name: str) -> tuple[SuiteSummary, ...]:
    """Find suites with exactly this name.

    :param connection: Open connection.
    :param name: Run name, compared case-sensitively.
    :returns: Matching suites ordered by result date, then hash.
    """
    return _find(connection, SUITE_TABLE.c.name == name, name)


def find_by_hash_prefix(
    connection: Connection,
    prefix: str,
    name: str | None,
) -> tuple[SuiteSummary, ...]:
    """Find suites whose hash starts with the prefix.

    :param connection: Open connection.
    :param prefix: Beginning of the hash, hex characters only.
    :param name: Required run name, or ``None`` for any name.
    :returns: Matching suites ordered by result date, then hash.
    """
    condition = SUITE_TABLE.c.hash.startswith(prefix)
    if name is not None:
        condition &= SUITE_TABLE.c.name == name
    return _find(connection, condition, name)


def _find(
    connection: Connection,
    condition: sa.ColumnElement[bool],
    name: str | None,
) -> tuple[SuiteSummary, ...]:
    rows = connection.execute(
        sa.select(
            SUITE_TABLE.c.hash,
            SUITE_TABLE.c.name,
            SUITE_TABLE.c.result_date,
        )
        .where(condition)
        .order_by(
            # SQLite and MariaDB sort NULL first, but NULL dates go last.
            sa.case((SUITE_TABLE.c.result_date.is_(None), 1), else_=0),
            SUITE_TABLE.c.result_date,
            SUITE_TABLE.c.hash,
        ),
    )
    return tuple(
        SuiteSummary(hash=row.hash, name=row.name, result_date=row.result_date)
        for row in rows
        # MariaDB compares utf8mb4 text ignoring case, so names are rechecked.
        if name is None or row.name == name
    )
