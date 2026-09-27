"""How a suite got into the database."""

from enum import StrEnum


class SuiteSource(StrEnum):
    """Command that stored the suite."""

    RUN = 'run'
    """Stored by ``takt run`` after it ran the benchmarks."""

    IMPORT = 'import'
    """Stored from an existing pyperf result file."""
