"""Choice of target databases from flags, environment and takt.toml."""

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from sqlalchemy.engine import URL, make_url

from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.model.target import Target
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.dialect_registry import dialect_for_url
from takt.infrastructure.config.sqlite_file_name import sqlite_file_name
from takt.infrastructure.config.toml_config_loader import load_config

_NamedUrl = tuple[str | None, str]

_MARIADB_PORT: Final = 3306


def resolve_targets(sources: ConfigSources) -> tuple[Target, ...]:
    """Resolve target databases from the highest-priority source.

    Flags replace ``TAKT_DB``, which replaces ``takt.toml`` targets.

    :param sources: Raw configuration inputs.
    :returns: Targets without duplicate databases, possibly empty; of
        several spellings of one database the first one is kept.
    :raises ConfigurationError: If the config file, a target name or a URL
        is invalid.
    """
    targets: dict[str, Target] = {}
    for name, url in _named_urls(sources, load_config(sources).targets):
        dialect = dialect_for_url(url).backend
        key = _database_key(url, dialect, sources.cwd)
        # Two sessions to one database in one transaction can deadlock.
        if key not in targets:
            targets[key] = Target(name=name, url=url, dialect=dialect)
    return tuple(targets.values())


def _database_key(url: str, dialect: str, cwd: Path) -> str:
    parsed = make_url(url)
    if dialect == 'sqlite':
        # A relative and an absolute path can name the same SQLite file.
        return str((cwd / sqlite_file_name(parsed)).resolve())
    # The driver, the user and the default port do not change the database.
    return URL.create(
        drivername=dialect,
        host=parsed.host,
        port=parsed.port or _MARIADB_PORT,
        database=parsed.database,
        query=parsed.query,
    ).render_as_string()


def _named_urls(
    sources: ConfigSources,
    config_targets: Mapping[str, str],
) -> list[_NamedUrl]:
    if sources.db_flags or sources.target_flags:
        flag_urls: list[_NamedUrl] = [(None, url) for url in sources.db_flags]
        flag_urls.extend(
            (name, _config_url(config_targets, name))
            for name in sources.target_flags
        )
        return flag_urls
    env_urls = sources.environ.get('TAKT_DB', '').split()
    if env_urls:
        return [(None, url) for url in env_urls]
    return list(config_targets.items())


def _config_url(config_targets: Mapping[str, str], name: str) -> str:
    if name not in config_targets:
        known = ', '.join(config_targets) or 'none'
        message = f'unknown target {name!r}; known targets: {known}'
        raise ConfigurationError(message)
    return config_targets[name]
