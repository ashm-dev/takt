"""Reader of pyperf result files."""

from pathlib import Path
from typing import Protocol

from takt.domain.model.suite import Suite


class ResultReader(Protocol):
    """Reader of pyperf result files."""

    def read(self, path: Path) -> Suite:
        """Read a pyperf JSON or JSON.gz result.

        :param path: Path to the result file.
        :returns: The suite from the file.
        :raises InvalidResultError: If the file cannot be read or parsed.
        """
