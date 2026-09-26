from dataclasses import replace
from pathlib import Path

import pytest

from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.naming.name_template import NameTemplate
from takt.infrastructure.config.resolve_name_template import (
    resolve_name_template,
)
from tests.domain.exact_pattern import exact_pattern
from tests.infrastructure.config.config_inputs import sources

EMPTY_NAME = 'run name must not be empty'


def write_template(tmp_path: Path, template: str) -> None:
    (tmp_path / 'takt.toml').write_text(
        f'name_template = "{template}"\n',
        encoding='utf-8',
    )


def test_flag_wins(tmp_path: Path) -> None:
    write_template(tmp_path, 'c')

    resolved = resolve_name_template(
        replace(
            sources(tmp_path),
            name_flag='a',
            environ={'TAKT_NAME': 'b'},
        ),
    )

    assert resolved == NameTemplate(text='a')


def test_env_wins_over_toml(tmp_path: Path) -> None:
    write_template(tmp_path, 'c')

    resolved = resolve_name_template(
        replace(sources(tmp_path), environ={'TAKT_NAME': 'b'}),
    )

    assert resolved == NameTemplate(text='b')


def test_blank_env_is_ignored(tmp_path: Path) -> None:
    write_template(tmp_path, 'c')

    resolved = resolve_name_template(
        replace(sources(tmp_path), environ={'TAKT_NAME': '  '}),
    )

    assert resolved == NameTemplate(text='c')


def test_toml(tmp_path: Path) -> None:
    write_template(tmp_path, 'c')

    assert resolve_name_template(sources(tmp_path)) == NameTemplate(text='c')


def test_none(tmp_path: Path) -> None:
    assert resolve_name_template(sources(tmp_path)) is None


def test_invalid_template_from_toml(tmp_path: Path) -> None:
    write_template(tmp_path, '')
    config = tmp_path / 'takt.toml'
    message = f'{config}: name_template: {EMPTY_NAME}'

    with pytest.raises(InvalidRunNameError, match=exact_pattern(message)):
        resolve_name_template(sources(tmp_path))


def test_invalid_template_from_env(tmp_path: Path) -> None:
    environ = {'TAKT_NAME': 'run:1'}
    message = "TAKT_NAME: run name must not contain ':': 'run:1'"

    with pytest.raises(InvalidRunNameError, match=exact_pattern(message)):
        resolve_name_template(replace(sources(tmp_path / 'x'), environ=environ))


def test_empty_flag(tmp_path: Path) -> None:
    with pytest.raises(InvalidRunNameError) as error:
        resolve_name_template(replace(sources(tmp_path), name_flag=''))

    assert str(error.value) == EMPTY_NAME
