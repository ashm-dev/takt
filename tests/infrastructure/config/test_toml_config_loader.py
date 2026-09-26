from dataclasses import replace
from pathlib import Path

import pytest

from takt.domain.errors.configuration_error import ConfigurationError
from takt.infrastructure.config.takt_config import TaktConfig
from takt.infrastructure.config.toml_config_loader import (
    load_config,
    load_toml_config,
)
from tests.domain.exact_pattern import exact_pattern
from tests.infrastructure.config.config_inputs import FULL_FILE, sources

EMPTY_CONFIG = TaktConfig(targets={}, name_template=None)


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    return tmp_path / 'takt.toml'


def test_full_file(config_file: Path) -> None:
    config_file.write_text(FULL_FILE, encoding='utf-8')

    config = load_toml_config(config_file)

    assert config.targets == {
        'local': 'sqlite:///bench.sqlite',
        'maria_ci': 'mariadb+pymysql://user:pass@db.local:3306/bench',
    }
    assert list(config.targets) == ['local', 'maria_ci']
    assert config.name_template == 'default {date}'


def test_empty_file(config_file: Path) -> None:
    config_file.write_text('', encoding='utf-8')

    assert load_toml_config(config_file) == EMPTY_CONFIG


def test_missing_file(config_file: Path) -> None:
    message = f'config file not found: {config_file}'

    with pytest.raises(ConfigurationError, match=exact_pattern(message)):
        load_toml_config(config_file)


def test_unreadable_file(config_file: Path) -> None:
    config_file.write_bytes(b'\xff\xfe')

    with pytest.raises(ConfigurationError) as error:
        load_toml_config(config_file)

    assert str(error.value).startswith(
        f'cannot read config file {config_file}: ',
    )


def test_invalid_toml(config_file: Path) -> None:
    config_file.write_text('name_template = \n', encoding='utf-8')

    with pytest.raises(ConfigurationError) as error:
        load_toml_config(config_file)

    assert str(error.value).startswith(f'{config_file}: invalid TOML: ')


@pytest.mark.parametrize(
    ('text', 'error'),
    [
        ('database = "x"\n', "unknown key 'database'"),
        ('name_template = 1\n', "'name_template' must be a string"),
        ('targets = "x"\n', "'targets' must be a table"),
        (
            '[targets.a]\nurl = "sqlite://"\npool = 1\n',
            "target 'a': unknown key 'pool'",
        ),
        ('[targets.a]\n', "target 'a': missing 'url'"),
        (
            '[targets.a]\nurl = "  "\n',
            "target 'a': 'url' must be a non-empty string",
        ),
        (
            '[targets.a]\nurl = 1\n',
            "target 'a': 'url' must be a non-empty string",
        ),
        ('targets = { a = 1 }\n', "target 'a' must be a table"),
    ],
)
def test_invalid_structure(config_file: Path, text: str, error: str) -> None:
    config_file.write_text(text, encoding='utf-8')
    message = f'{config_file}: {error}'

    with pytest.raises(ConfigurationError, match=exact_pattern(message)):
        load_toml_config(config_file)


@pytest.mark.parametrize(
    ('key', 'name'),
    [('"bad name"', 'bad name'), (r'"ci\n"', 'ci\n')],
)
def test_bad_target_name(config_file: Path, key: str, name: str) -> None:
    config_file.write_text(
        f'[targets.{key}]\nurl = "sqlite://"\n',
        encoding='utf-8',
    )
    message = (
        f'{config_file}: invalid target name {name!r}; '
        "use letters, digits, '_' and '-'"
    )

    with pytest.raises(ConfigurationError, match=exact_pattern(message)):
        load_toml_config(config_file)


def test_load_config_default_missing(tmp_path: Path) -> None:
    assert load_config(sources(tmp_path)) == EMPTY_CONFIG


def test_load_config_default_present(
    tmp_path: Path,
    config_file: Path,
) -> None:
    config_file.write_text(FULL_FILE, encoding='utf-8')

    assert load_config(sources(tmp_path)).name_template == 'default {date}'


def test_load_config_explicit_missing(tmp_path: Path) -> None:
    path = tmp_path / 'x.toml'

    with pytest.raises(ConfigurationError) as error:
        load_config(replace(sources(tmp_path), config_path=path))

    assert str(error.value) == f'config file not found: {path}'
