"""Open transaction in one target database."""

from typing import Protocol

from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.suite_summary import SuiteSummary


class TargetSession(Protocol):
    """Open transaction in one target database."""

    def loaded_name(self, suite_hash: str) -> tuple[bool, str | None]:
        """Check whether the suite is already stored.

        :param suite_hash: Suite hash.
        :returns: Whether the suite is stored and its name.
        """

    def insert(self, record: SuiteRecord) -> None:
        """Insert the whole suite.

        :param record: Suite with storage attributes.
        """

    def delete(self, suite_hash: str) -> None:
        """Delete the suite from every table.

        :param suite_hash: Suite hash.
        """

    def get(self, suite_hash: str) -> SuiteRecord:
        """Read the whole suite.

        :param suite_hash: Suite hash.
        :returns: The stored suite.
        """

    def find_by_name(self, name: str) -> tuple[SuiteSummary, ...]:
        """Find suites with exactly this name.

        :param name: Run name.
        :returns: Matching suites ordered by result date, then hash.
        """

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

    def commit(self) -> None:
        """Commit the transaction."""

    def rollback(self) -> None:
        """Roll back the transaction."""

    def close(self) -> None:
        """Release the connection."""
