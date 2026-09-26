"""Target session backed by one SQLAlchemy transaction."""

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine, RootTransaction
from sqlalchemy.exc import SQLAlchemyError

from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.suite_summary import SuiteSummary
from takt.infrastructure.db import suite_finder
from takt.infrastructure.db.database_error import database_error
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
        # The session does not know its Target, so the engine URL labels it.
        label = engine.url.render_as_string(hide_password=True)
        self._read_failure = f'cannot read from database {label}'
        self._write_failure = f'cannot write to database {label}'
        self._commit_failure = f'cannot commit to database {label}'

    def loaded_name(self, suite_hash: str) -> tuple[bool, str | None]:
        """Check whether the suite hash was ever stored.

        :param suite_hash: Suite hash.
        :returns: Whether the hash is stored and the suite name.
        :raises ExecutionError: If the database cannot be read.
        """
        try:
            return self._loaded_name(suite_hash)
        except SQLAlchemyError as error:
            raise database_error(self._read_failure, error) from error

    def insert(self, record: SuiteRecord) -> None:
        """Insert the whole suite.

        :param record: Suite with storage attributes.
        :raises ExecutionError: If the database cannot be written.
        """
        try:
            insert_suite(self._connection, record)
        except SQLAlchemyError as error:
            raise database_error(self._write_failure, error) from error

    def delete(self, suite_hash: str) -> None:
        """Delete the suite from every table.

        :param suite_hash: Suite hash.
        :raises ExecutionError: If the database cannot be written.
        """
        try:
            delete_suite(self._connection, suite_hash)
        except SQLAlchemyError as error:
            raise database_error(self._write_failure, error) from error

    def get(self, suite_hash: str) -> SuiteRecord:
        """Read the whole suite.

        :param suite_hash: Suite hash.
        :returns: The stored suite.
        :raises OperandNotFoundError: If the suite is not stored.
        :raises ExecutionError: If the database cannot be read.
        """
        try:
            record = read_suite(self._connection, suite_hash)
        except SQLAlchemyError as error:
            raise database_error(self._read_failure, error) from error
        if record is None:
            msg = f'suite {suite_hash} not found'
            raise OperandNotFoundError(msg)
        return record

    def find_by_name(self, name: str) -> tuple[SuiteSummary, ...]:
        """Find suites with exactly this name.

        :param name: Run name.
        :returns: Matching suites ordered by result date, then hash.
        :raises ExecutionError: If the database cannot be read.
        """
        try:
            return suite_finder.find_by_name(self._connection, name)
        except SQLAlchemyError as error:
            raise database_error(self._read_failure, error) from error

    def find_by_hash_prefix(
        self,
        prefix: str,
        name: str | None,
    ) -> tuple[SuiteSummary, ...]:
        """Find suites whose hash starts with the prefix.

        :param prefix: Beginning of the hash.
        :param name: Required run name, or ``None`` for any name.
        :returns: Matching suites ordered by result date, then hash.
        :raises ExecutionError: If the database cannot be read.
        """
        try:
            return suite_finder.find_by_hash_prefix(
                self._connection,
                prefix,
                name,
            )
        except SQLAlchemyError as error:
            raise database_error(self._read_failure, error) from error

    def commit(self) -> None:
        """Commit the transaction.

        :raises ExecutionError: If the database rejects the commit.
        """
        try:
            self._transaction.commit()
        except SQLAlchemyError as error:
            raise database_error(self._commit_failure, error) from error

    def rollback(self) -> None:
        """Roll back the transaction if it is still active."""
        if self._transaction.is_active:
            self._transaction.rollback()

    def close(self) -> None:
        """Close the connection and release the engine."""
        self._connection.close()
        self._engine.dispose()

    def _loaded_name(self, suite_hash: str) -> tuple[bool, str | None]:
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
