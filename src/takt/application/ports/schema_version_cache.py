"""Local cache of schema revisions per target."""

from typing import Protocol


class SchemaVersionCache(Protocol):
    """Local cache of schema revisions per target."""

    def get(self, url: str) -> str | None:
        """Return the cached revision.

        :param url: Target URL.
        :returns: Cached revision or ``None``.
        """

    def put(self, url: str, revision: str) -> None:
        """Store the revision.

        :param url: Target URL.
        :param revision: Schema revision of the target.
        """

    def forget(self, url: str) -> None:
        """Remove the cached revision.

        :param url: Target URL.
        """
