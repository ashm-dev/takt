"""Deletion of a whole suite from the takt tables."""

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from takt.infrastructure.db.schema.tables import (
    BENCHMARK_TABLE,
    LOADED_HASH_TABLE,
    MEASUREMENT_TABLE,
    RUN_METADATA_TABLE,
    SUITE_TABLE,
    WORKER_RUN_TABLE,
)


def delete_suite(connection: Connection, suite_hash: str) -> None:
    """Delete every row of a suite without committing.

    Child tables go first so that foreign keys stay valid.

    :param connection: Connection with an open transaction.
    :param suite_hash: Suite hash; a missing hash deletes nothing.
    """
    for child in (
        MEASUREMENT_TABLE,
        RUN_METADATA_TABLE,
        WORKER_RUN_TABLE,
        BENCHMARK_TABLE,
    ):
        connection.execute(
            sa.delete(child).where(child.c.suite_hash == suite_hash),
        )
    for parent in (SUITE_TABLE, LOADED_HASH_TABLE):
        condition = parent.c.hash == suite_hash
        connection.execute(sa.delete(parent).where(condition))
