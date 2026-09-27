"""Choice of target databases from flags, environment and takt.toml."""

from pathlib import Path
from typing import Final

from sqlalchemy.engine import URL, make_url

from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.model.target import Target
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.dialect_registry import dialect_for_url
from takt.infrastructure.config.sqlite_file_name import sqlite_file_name
from takt.infrastructure.config.takt_config import TaktConfig
from takt.infrastructure.config.toml_config_loader import load_config

_NamedUrl = tuple[str | None, str, str | None]
"""Target name, URL, and where the URL came from unless the user typed it."""

_MARIADB_PORT: Final = 3306
"""Port that MariaDB uses when a URL has none."""


def resolve_targets(sources: ConfigSources) -> tuple[Target, ...]:
    """Resolve target databases from the highest-priority source.

    Flags replace ``TAKT_DB``, which replaces ``takt.toml`` targets.

    :param sources: Raw configuration inputs.
    :returns: Targets without duplicate databases, possibly empty; of
        several spellings of one database the first one is kept.
    :raises ConfigurationError: If the config file, a target name or a URL
        is invalid; an error in a URL from ``TAKT_DB`` or ``takt.toml``
        starts with that source.
    """
    targets: dict[str, Target] = {}
    for name, url, origin in _named_urls(sources, load_config(sources)):
        target = Target(name=name, url=url, dialect=_dialect(url, origin))
        # Two sessions to one database in one transaction can deadlock.
        targets.setdefault(_database_key(target, sources.cwd), target)
    return tuple(targets.values())


def _dialect(url: str, origin: str | None) -> str:
    try:
        return dialect_for_url(url).backend
    except ConfigurationError as error:
        if origin is None:
            raise
        message = f'{origin}: {error}'
        raise type(error)(message) from None


def _database_key(target: Target, cwd: Path) -> str:
    parsed = make_url(target.url)
    if target.dialect == 'sqlite':
        # A relative and an absolute path can name the same SQLite file.
        return str((cwd / sqlite_file_name(parsed)).resolve())
    # The driver, the user and the default port do not change the database.
    return URL.create(
        drivername=target.dialect,
        host=parsed.host,
        port=parsed.port or _MARIADB_PORT,
        database=parsed.database,
        query=parsed.query,
    ).render_as_string()


def _named_urls(sources: ConfigSources, config: TaktConfig) -> list[_NamedUrl]:
    if sources.db_flags or sources.target_flags:
        flag_urls: list[_NamedUrl] = [
            (None, url, None) for url in sources.db_flags
        ]
        flag_urls.extend(
            _config_target(config, name, sources.cwd)
            for name in sources.target_flags
        )
        return flag_urls
    env_urls = sources.environ.get('TAKT_DB', '').split()
    if env_urls:
        return [(None, url, 'TAKT_DB') for url in env_urls]
    return [
        _config_target(config, name, sources.cwd) for name in config.targets
    ]


def _config_target(config: TaktConfig, name: str, cwd: Path) -> _NamedUrl:
    if name not in config.targets:
        raise ConfigurationError(_unknown_target(config, name, cwd))
    return (name, config.targets[name], f'{config.path}: target {name!r}')


def _unknown_target(config: TaktConfig, name: str, cwd: Path) -> str:
    # Running from the wrong folder is the usual reason for no targets.
    if config.path is None:
        return (
            f'unknown target {name!r}: no takt.toml in {cwd}; use --config PATH'
        )
    known = ', '.join(config.targets) or 'none'
    return f'unknown target {name!r}; known targets: {known}'
