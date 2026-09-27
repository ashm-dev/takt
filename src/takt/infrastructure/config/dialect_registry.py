"""Supported database dialects and URL checks."""

from collections.abc import Mapping
from importlib import util
from types import MappingProxyType
from typing import Final

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.missing_driver_error import MissingDriverError
from takt.domain.errors.unsupported_dialect_error import (
    UnsupportedDialectError,
)
from takt.infrastructure.config.dialect_info import DialectInfo
from takt.infrastructure.config.sqlite_file_name import sqlite_file_name

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
"""Supported dialects by the backend name at the start of a URL."""


def dialect_for_url(url: str) -> DialectInfo:
    """Check that a database URL is supported and its driver is installed.

    :param url: SQLAlchemy URL as the user wrote it.
    :returns: The dialect of the URL.
    :raises ConfigurationError: If the URL cannot be parsed, or a SQLite
        URL has a host instead of a file path or names an in-memory
        database.
    :raises UnsupportedDialectError: If the backend or driver is not
        supported.
    :raises MissingDriverError: If the driver package is not installed.
    """
    parsed = _parse(url)
    # get_driver_name() imports the driver, so the name is split by hand.
    backend, _, driver = parsed.drivername.partition('+')
    dialect = DIALECTS.get(backend)
    if dialect is None:
        message = (
            f'unsupported database {backend!r}; '
            'supported in this version: mariadb, sqlite'
        )
        raise UnsupportedDialectError(message)
    _check_driver(dialect, driver)
    if backend == 'sqlite':
        _check_sqlite_file(url, parsed)
    _check_installed(dialect)
    return dialect


def _parse(url: str) -> URL:
    try:
        return make_url(url)
    except ArgumentError, ValueError:
        raise _invalid_url(url) from None


def _check_sqlite_file(url: str, parsed: URL) -> None:
    # sqlite://bench.db puts the file name where the host goes.
    if parsed.host:
        raise _invalid_url(url)
    database = sqlite_file_name(parsed)
    in_memory = parsed.query.get('mode') == 'memory'
    # Every connection gets a new empty in-memory database, and it is gone
    # when takt exits.
    if not database or database == ':memory:' or in_memory:
        message = (
            f'in-memory SQLite cannot store results: {url!r}; '
            'use a file URL such as sqlite:///bench.db'
        )
        raise ConfigurationError(message)


def _invalid_url(url: str) -> ConfigurationError:
    return ConfigurationError(
        f'invalid database URL: {url!r}; expected a URL such as '
        'sqlite:///bench.db or mariadb+pymysql://user:password@host/db',
    )


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
