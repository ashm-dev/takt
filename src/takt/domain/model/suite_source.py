"""How a suite got into the database."""

from enum import StrEnum


class SuiteSource(StrEnum):
    """Command that stored the suite."""

    RUN = 'run'
    IMPORT = 'import'
