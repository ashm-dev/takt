"""Column types shared by the takt tables."""

from typing import Final

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

_HASH_LENGTH: Final = 64
_NAME_LENGTH: Final = 255
_SHORT_TEXT_LENGTH: Final = 16
_KIND_LENGTH: Final = 8

HASH_TYPE: Final = sa.CHAR(_HASH_LENGTH)
NAME_TYPE: Final = sa.String(_NAME_LENGTH)
FORMAT_VERSION_TYPE: Final = sa.String(_SHORT_TEXT_LENGTH)
SOURCE_TYPE: Final = sa.String(_SHORT_TEXT_LENGTH)
KIND_TYPE: Final = sa.String(_KIND_LENGTH)
POSITION_TYPE: Final = sa.Integer()
LOOPS_TYPE: Final = sa.BigInteger()
DATETIME_TYPE: Final = sa.DateTime().with_variant(
    mysql.DATETIME(fsp=6),
    'mariadb',
)
DOUBLE_TYPE: Final[sa.Double[float]] = sa.Double()
TEXT_TYPE: Final = sa.Text()
BIGINT_TYPE: Final = sa.BigInteger()
JSON_TYPE: Final = sa.JSON()
