"""Loading of takt settings from a takt.toml file."""

import re
import tomllib
from pathlib import Path
from typing import Final, NoReturn

from takt.domain.errors.configuration_error import ConfigurationError
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.takt_config import TaktConfig

_DEFAULT_FILE_NAME: Final = 'takt.toml'
_TOP_KEYS: Final = frozenset(('name_template', 'targets'))
_TARGET_KEYS: Final = frozenset(('url',))
_TARGET_NAME: Final = re.compile('[A-Za-z0-9_-]+')


def load_toml_config(path: Path) -> TaktConfig:
    """Read and validate a ``takt.toml`` file.

    :param path: Path to the config file.
    :returns: Targets and the run name template from the file.
    :raises ConfigurationError: If the file is missing, unreadable, not
        valid TOML or has an unexpected structure.
    """
    document = _read_document(path)
    for key in document:
        if key not in _TOP_KEYS:
            _fail(f'{path}: unknown key {key!r}')
    name_template = document.get('name_template')
    if name_template is not None and not isinstance(name_template, str):
        _fail(f"{path}: 'name_template' must be a string")
    return TaktConfig(
        targets=_read_targets(path, document.get('targets', {})),
        name_template=name_template,
    )


def load_config(sources: ConfigSources) -> TaktConfig:
    """Load the explicit config file or ``takt.toml`` from the cwd.

    :param sources: Raw configuration inputs.
    :returns: The loaded config, or an empty one without a default file.
    :raises ConfigurationError: If the config file is missing or invalid.
    """
    if sources.config_path is not None:
        return load_toml_config(sources.config_path)
    default = sources.cwd / _DEFAULT_FILE_NAME
    if default.is_file():
        return load_toml_config(default)
    return TaktConfig(targets={}, name_template=None)


def _read_document(path: Path) -> dict[str, object]:
    try:
        text = path.read_bytes().decode('utf-8')
    except FileNotFoundError:
        _fail(f'config file not found: {path}')
    except (OSError, UnicodeDecodeError) as exc:
        _fail(f'cannot read config file {path}: {exc}')
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        _fail(f'{path}: invalid TOML: {exc}')


def _read_targets(path: Path, raw_targets: object) -> dict[str, str]:
    if not isinstance(raw_targets, dict):
        _fail(f"{path}: 'targets' must be a table")
    tables: dict[str, object] = raw_targets
    targets: dict[str, str] = {}
    for name, table in tables.items():
        targets[name] = _read_target_url(path, name, table)
    return targets


def _read_target_url(path: Path, name: str, table: object) -> str:
    if _TARGET_NAME.fullmatch(name) is None:
        _fail(
            f'{path}: invalid target name {name!r}; '
            "use letters, digits, '_' and '-'",
        )
    if not isinstance(table, dict):
        _fail(f'{path}: target {name!r} must be a table')
    fields: dict[str, object] = table
    for key in fields:
        if key not in _TARGET_KEYS:
            _fail(f'{path}: target {name!r}: unknown key {key!r}')
    if 'url' not in fields:
        _fail(f"{path}: target {name!r}: missing 'url'")
    url = fields['url']
    if not isinstance(url, str) or not url.strip():
        _fail(f"{path}: target {name!r}: 'url' must be a non-empty string")
    return url


def _fail(message: str) -> NoReturn:
    raise ConfigurationError(message) from None
