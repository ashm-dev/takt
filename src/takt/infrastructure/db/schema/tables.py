"""SQLAlchemy Core description of every takt table.

The whole schema lives in one module because Alembic and the repository
work with all tables at once.
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

import sqlalchemy as sa

from takt.domain.model.metadata_key_types import METADATA_KEY_TYPES
from takt.domain.model.metadata_value import MetadataValue
from takt.infrastructure.db.schema import column_types

METADATA: Final = sa.MetaData(
    naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    },
)

_ENGINE: Final = 'InnoDB'
_CHARSET: Final = 'utf8mb4'
_SUITE_HASH: Final = 'suite_hash'
_BENCHMARK_POSITION: Final = 'benchmark_position'
_RUN_POSITION: Final = 'run_position'

_NumberType = sa.BigInteger | sa.Double[float]
_MetadataType = _NumberType | sa.JSON | sa.Text
_ColumnTypes = Mapping[type[MetadataValue], _MetadataType]

_METADATA_COLUMN_TYPES: Final[_ColumnTypes] = MappingProxyType(
    {
        int: column_types.BIGINT_TYPE,
        float: column_types.DOUBLE_TYPE,
        str: column_types.TEXT_TYPE,
        tuple: column_types.JSON_TYPE,
    }
)


def _hash_column(name: str) -> sa.Column[str]:
    return sa.Column(name, column_types.HASH_TYPE, primary_key=True)


def _position_column(name: str) -> sa.Column[int]:
    return sa.Column(
        name,
        column_types.POSITION_TYPE,
        primary_key=True,
        autoincrement=False,
    )


def _run_key_columns() -> tuple[sa.Column[str] | sa.Column[int], ...]:
    return (
        _hash_column(_SUITE_HASH),
        _position_column(_BENCHMARK_POSITION),
        _position_column(_RUN_POSITION),
    )


def _parent_key(parent: sa.Table) -> sa.ForeignKeyConstraint:
    referred = list(parent.primary_key.columns)
    return sa.ForeignKeyConstraint(
        [column.name for column in referred],
        referred,
    )


SUITE_TABLE: Final[sa.Table] = sa.Table(
    'takt_suite',
    METADATA,
    _hash_column('hash'),
    sa.Column('name', column_types.NAME_TYPE, nullable=True),
    sa.Column(
        'format_version',
        column_types.FORMAT_VERSION_TYPE,
        nullable=False,
    ),
    sa.Column('source', column_types.SOURCE_TYPE, nullable=False),
    sa.Column('result_date', column_types.DATETIME_TYPE, nullable=True),
    sa.Column('loaded_at', column_types.DATETIME_TYPE, nullable=False),
    sa.Index(None, 'name'),
    sa.Index(None, 'result_date'),
    mariadb_engine=_ENGINE,
    mariadb_charset=_CHARSET,
)

BENCHMARK_TABLE: Final[sa.Table] = sa.Table(
    'takt_benchmark',
    METADATA,
    _hash_column(_SUITE_HASH),
    _position_column(_BENCHMARK_POSITION),
    sa.Column('name', column_types.NAME_TYPE, nullable=False),
    sa.ForeignKeyConstraint([_SUITE_HASH], [SUITE_TABLE.c.hash]),
    mariadb_engine=_ENGINE,
    mariadb_charset=_CHARSET,
)

WORKER_RUN_TABLE: Final[sa.Table] = sa.Table(
    'takt_worker_run',
    METADATA,
    *_run_key_columns(),
    _parent_key(BENCHMARK_TABLE),
    mariadb_engine=_ENGINE,
    mariadb_charset=_CHARSET,
)

MEASUREMENT_TABLE: Final[sa.Table] = sa.Table(
    'takt_measurement',
    METADATA,
    *_run_key_columns(),
    sa.Column('kind', column_types.KIND_TYPE, primary_key=True),
    _position_column('position'),
    sa.Column('loops', column_types.LOOPS_TYPE, nullable=True),
    sa.Column('value', column_types.DOUBLE_TYPE, nullable=False),
    _parent_key(WORKER_RUN_TABLE),
    mariadb_engine=_ENGINE,
    mariadb_charset=_CHARSET,
)

RUN_METADATA_TABLE: Final[sa.Table] = sa.Table(
    'takt_run_metadata',
    METADATA,
    *_run_key_columns(),
    *(
        sa.Column(key, _METADATA_COLUMN_TYPES[key_type], nullable=True)
        for key, key_type in METADATA_KEY_TYPES.items()
    ),
    sa.Column('custom', column_types.JSON_TYPE, nullable=True),
    _parent_key(WORKER_RUN_TABLE),
    mariadb_engine=_ENGINE,
    mariadb_charset=_CHARSET,
)

LOADED_HASH_TABLE: Final[sa.Table] = sa.Table(
    'takt_loaded_hash',
    METADATA,
    _hash_column('hash'),
    mariadb_engine=_ENGINE,
    mariadb_charset=_CHARSET,
)
