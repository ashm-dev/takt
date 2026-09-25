from pathlib import Path

import pytest

from takt.domain.errors.configuration_error import ConfigurationError
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.takt_config import TaktConfig
from takt.infrastructure.config.toml_config_loader import (
    load_config,
    load_toml_config,
)

FULL_FILE = """\
name_template = "default {date}"

[targets.local]
url = "sqlite:///bench.sqlite"

[targets.maria_ci]
url = "mariadb+pymysql://user:pass@db.local:3306/bench"
"""

EMPTY_CONFIG = TaktConfig(targets={}, name_template=None)


def sources(tmp_path: Path, config_path: Path | None = None) -> ConfigSources:
    return ConfigSources(
        db_flags=(),
        target_flags=(),
        config_path=config_path,
        name_flag=None,
        environ={},
        cwd=tmp_path,
    )


def config_error(path: Path, text: str | None = None) -> str:
    if text is not None:
        path.write_text(text, encoding='utf-8')
    try:
        load_toml_config(path)
    except ConfigurationError as error:
        return str(error)
    pytest.fail('ConfigurationError was not raised')


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
    assert config_error(config_file) == (
        f'config file not found: {config_file}'
    )


def test_unreadable_file(config_file: Path) -> None:
    config_file.write_bytes(b'\xff\xfe')

    assert config_error(config_file).startswith(
        f'cannot read config file {config_file}: ',
    )


def test_invalid_toml(config_file: Path) -> None:
    assert config_error(config_file, 'name_template = \n').startswith(
        f'{config_file}: invalid TOML: ',
    )


def test_unknown_top_key(config_file: Path) -> None:
    assert config_error(config_file, 'database = "x"\n') == (
        f"{config_file}: unknown key 'database'"
    )


def test_name_template_not_string(config_file: Path) -> None:
    assert config_error(config_file, 'name_template = 1\n') == (
        f"{config_file}: 'name_template' must be a string"
    )


def test_targets_not_table(config_file: Path) -> None:
    assert config_error(config_file, 'targets = "x"\n') == (
        f"{config_file}: 'targets' must be a table"
    )


def test_bad_target_name(config_file: Path) -> None:
    text = '[targets."bad name"]\nurl = "sqlite://"\n'

    assert config_error(config_file, text) == (
        f"{config_file}: invalid target name 'bad name'; "
        "use letters, digits, '_' and '-'"
    )


def test_target_unknown_key(config_file: Path) -> None:
    text = '[targets.a]\nurl = "sqlite://"\npool = 1\n'

    assert config_error(config_file, text) == (
        f"{config_file}: target 'a': unknown key 'pool'"
    )


def test_target_missing_url(config_file: Path) -> None:
    assert config_error(config_file, '[targets.a]\n') == (
        f"{config_file}: target 'a': missing 'url'"
    )


def test_target_empty_url(config_file: Path) -> None:
    assert config_error(config_file, '[targets.a]\nurl = "  "\n') == (
        f"{config_file}: target 'a': 'url' must be a non-empty string"
    )


def test_target_not_table(config_file: Path) -> None:
    assert config_error(config_file, 'targets = { a = 1 }\n') == (
        f"{config_file}: target 'a' must be a table"
    )


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
        load_config(sources(tmp_path, config_path=path))

    assert str(error.value) == f'config file not found: {path}'
