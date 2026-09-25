"""Choice of target databases from flags, environment and takt.toml."""

from collections.abc import Mapping

from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.model.target import Target
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.dialect_registry import dialect_for_url
from takt.infrastructure.config.toml_config_loader import load_config

_NamedUrl = tuple[str | None, str]


def resolve_targets(sources: ConfigSources) -> tuple[Target, ...]:
    """Resolve target databases from the highest-priority source.

    Flags replace ``TAKT_DB``, which replaces ``takt.toml`` targets.

    :param sources: Raw configuration inputs.
    :returns: Targets without duplicate URLs, possibly empty.
    :raises ConfigurationError: If the config file, a target name or a URL
        is invalid.
    """
    config_targets = load_config(sources).targets
    targets: dict[str, Target] = {}
    for name, url in _named_urls(sources, config_targets):
        # Two sessions to one database in one transaction can deadlock.
        if url not in targets:
            targets[url] = Target(
                name=name,
                url=url,
                dialect=dialect_for_url(url).backend,
            )
    return tuple(targets.values())


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
