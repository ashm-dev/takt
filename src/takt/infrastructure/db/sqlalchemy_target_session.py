"""Target session backed by one SQLAlchemy transaction."""

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine, RootTransaction

from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.suite_summary import SuiteSummary
from takt.infrastructure.db import suite_finder
from takt.infrastructure.db.schema.tables import LOADED_HASH_TABLE, SUITE_TABLE
from takt.infrastructure.db.suite_row_deleter import delete_suite
from takt.infrastructure.db.suite_row_reader import read_suite
from takt.infrastructure.db.suite_row_writer import insert_suite


class SqlAlchemyTargetSession:
    """Open transaction in one target database."""

    def __init__(
        self,
        *,
        engine: Engine,
        connection: Connection,
        transaction: RootTransaction,
    ) -> None:
        """Wrap an already started transaction.

        :param engine: Engine that owns the connection.
        :param connection: Connection of the transaction.
        :param transaction: Started root transaction.
        """
        self._engine = engine
        self._connection = connection
        self._transaction = transaction

    def loaded_name(self, suite_hash: str) -> tuple[bool, str | None]:
        """Check whether the suite hash was ever stored.

        :param suite_hash: Suite hash.
        :returns: Whether the hash is stored and the suite name.
        """
        loaded = self._connection.execute(
            sa.select(LOADED_HASH_TABLE.c.hash).where(
                LOADED_HASH_TABLE.c.hash == suite_hash,
            ),
        ).first()
        if loaded is None:
            return (False, None)
        name: str | None = self._connection.execute(
            sa.select(SUITE_TABLE.c.name).where(
                SUITE_TABLE.c.hash == suite_hash,
            ),
        ).scalar()
        return (True, name)

    def insert(self, record: SuiteRecord) -> None:
        """Insert the whole suite.

        :param record: Suite with storage attributes.
        """
        insert_suite(self._connection, record)

    def delete(self, suite_hash: str) -> None:
        """Delete the suite from every table.

        :param suite_hash: Suite hash.
        """
        delete_suite(self._connection, suite_hash)

    def get(self, suite_hash: str) -> SuiteRecord:
        """Read the whole suite.

        :param suite_hash: Suite hash.
        :returns: The stored suite.
        :raises OperandNotFoundError: If the suite is not stored.
        """
        record = read_suite(self._connection, suite_hash)
        if record is None:
            msg = f'suite {suite_hash} not found'
            raise OperandNotFoundError(msg)
        return record

    def find_by_name(self, name: str) -> tuple[SuiteSummary, ...]:
        """Find suites with exactly this name.

        :param name: Run name.
        :returns: Matching suites ordered by result date, then hash.
        """
        return suite_finder.find_by_name(self._connection, name)

    def find_by_hash_prefix(
        self,
        prefix: str,
        name: str | None,
    ) -> tuple[SuiteSummary, ...]:
        """Find suites whose hash starts with the prefix.

        :param prefix: Beginning of the hash.
        :param name: Required run name, or ``None`` for any name.
        :returns: Matching suites ordered by result date, then hash.
        """
        return suite_finder.find_by_hash_prefix(self._connection, prefix, name)

    def commit(self) -> None:
        """Commit the transaction."""
        self._transaction.commit()

    def rollback(self) -> None:
        """Roll back the transaction if it is still active."""
        if self._transaction.is_active:
            self._transaction.rollback()

    def close(self) -> None:
        """Close the connection and release the engine."""
        self._connection.close()
        self._engine.dispose()
