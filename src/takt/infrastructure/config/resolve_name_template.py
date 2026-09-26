"""Choice of the run name template from flags, environment and takt.toml."""

from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.naming.name_template import NameTemplate
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.toml_config_loader import load_config


def resolve_name_template(sources: ConfigSources) -> NameTemplate | None:
    """Resolve the run name template from the highest-priority source.

    ``--name`` replaces ``TAKT_NAME``, which replaces ``takt.toml``.

    :param sources: Raw configuration inputs.
    :returns: The parsed template, or ``None`` if no source sets it.
    :raises InvalidRunNameError: If the chosen template is invalid; a
        value from ``TAKT_NAME`` or ``takt.toml`` is prefixed with its
        source.
    :raises ConfigurationError: If the config file is missing or invalid.
    """
    if sources.name_flag is not None:
        return NameTemplate.parse(sources.name_flag)
    env = sources.environ.get('TAKT_NAME')
    if env is not None and env.strip():
        return _parse(env, 'TAKT_NAME')
    config = load_config(sources)
    if config.name_template is not None:
        return _parse(config.name_template, f'{config.path}: name_template')
    return None


def _parse(text: str, source: str) -> NameTemplate:
    # The user did not type this value, so the error says where it lives.
    try:
        return NameTemplate.parse(text)
    except InvalidRunNameError as error:
        message = f'{source}: {error}'
        raise InvalidRunNameError(message) from None
