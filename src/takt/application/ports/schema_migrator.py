"""Migrator of the takt schema."""

from typing import Protocol

from takt.domain.model.target import Target


class SchemaMigrator(Protocol):
    """Migrator of the takt schema."""

    def head(self, target: Target) -> str:
        """Return the latest schema revision without touching the database.

        :param target: Target database.
        :returns: Latest revision for the target dialect.
        """

    def upgrade(self, target: Target) -> None:
        """Bring the database schema to the latest revision.

        :param target: Target database.
        """
