"""Column types shared by the takt tables."""

from typing import Final

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

_HASH_LENGTH: Final = 64
"""Length of a SHA-256 hex digest."""

_NAME_LENGTH: Final = 255
"""Longest suite or benchmark name that fits in a column."""

_SHORT_TEXT_LENGTH: Final = 16
"""Longest format version or source value."""

_KIND_LENGTH: Final = 8
"""Longest measurement kind, ``"warmup"`` or ``"value"``."""

HASH_TYPE: Final = sa.CHAR(_HASH_LENGTH)
"""Type of a result hash column."""

NAME_TYPE: Final = sa.String(_NAME_LENGTH)
"""Type of a suite or benchmark name column."""

FORMAT_VERSION_TYPE: Final = sa.String(_SHORT_TEXT_LENGTH)
"""Type of the pyperf format version column."""

SOURCE_TYPE: Final = sa.String(_SHORT_TEXT_LENGTH)
"""Type of the column with the command that stored a suite."""

KIND_TYPE: Final = sa.String(_KIND_LENGTH)
"""Type of the measurement kind column."""

POSITION_TYPE: Final = sa.Integer()
"""Type of a column with the order of a row inside its parent."""

LOOPS_TYPE: Final = sa.BigInteger()
"""Type of the loop count of a measurement."""

DATETIME_TYPE: Final = sa.DateTime().with_variant(
    mysql.DATETIME(fsp=6),
    'mariadb',
)
"""Type of a date column, with microseconds on MariaDB."""

DOUBLE_TYPE: Final[sa.Double[float]] = sa.Double()
"""Type of a float metadata or measurement value."""

TEXT_TYPE: Final = sa.Text()
"""Type of a text metadata value."""

BIGINT_TYPE: Final = sa.BigInteger()
"""Type of an integer metadata value."""

JSON_TYPE: Final = sa.JSON()
"""Type of a list or custom metadata value stored as JSON."""
