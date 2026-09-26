"""Supported database dialects and URL checks."""

from collections.abc import Mapping
from importlib import util
from types import MappingProxyType
from typing import Final

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.missing_driver_error import MissingDriverError
from takt.domain.errors.unsupported_dialect_error import (
    UnsupportedDialectError,
)
from takt.infrastructure.config.dialect_info import DialectInfo

DIALECTS: Final[Mapping[str, DialectInfo]] = MappingProxyType(
    {
        'sqlite': DialectInfo(
            backend='sqlite',
            allowed_drivers=('pysqlite',),
            driver_module=None,
            extra=None,
        ),
        'mariadb': DialectInfo(
            backend='mariadb',
            allowed_drivers=('pymysql',),
            driver_module='pymysql',
            extra='mariadb',
        ),
    }
)


def dialect_for_url(url: str) -> DialectInfo:
    """Check that a database URL is supported and its driver is installed.

    :param url: SQLAlchemy URL as the user wrote it.
    :returns: The dialect of the URL.
    :raises ConfigurationError: If the URL cannot be parsed.
    :raises UnsupportedDialectError: If the backend or driver is not
        supported.
    :raises MissingDriverError: If the driver package is not installed.
    """
    backend, driver = _split_drivername(url)
    dialect = DIALECTS.get(backend)
    if dialect is None:
        message = (
            f'unsupported database {backend!r}; '
            'supported in this version: mariadb, sqlite'
        )
        raise UnsupportedDialectError(message)
    _check_driver(dialect, driver)
    _check_installed(dialect)
    return dialect


def _split_drivername(url: str) -> tuple[str, str]:
    try:
        drivername = make_url(url).drivername
    except ArgumentError, ValueError:
        message = f'invalid database URL: {url!r}'
        raise ConfigurationError(message) from None
    # get_driver_name() imports the driver, so the name is split by hand.
    backend, _, driver = drivername.partition('+')
    return backend, driver


def _check_driver(dialect: DialectInfo, driver: str) -> None:
    if driver and driver not in dialect.allowed_drivers:
        supported = ', '.join(dialect.allowed_drivers)
        message = (
            f'unsupported driver {driver!r} for {dialect.backend}; '
            f'supported: {supported}'
        )
        raise UnsupportedDialectError(message)


def _check_installed(dialect: DialectInfo) -> None:
    module = dialect.driver_module
    if module is not None and util.find_spec(module) is None:
        message = (
            f'database driver {module!r} for {dialect.backend} '
            f"is not installed; run: pip install 'takt[{dialect.extra}]'"
        )
        raise MissingDriverError(message)
