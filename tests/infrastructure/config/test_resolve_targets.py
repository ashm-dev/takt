from collections.abc import Mapping
from pathlib import Path

import pytest

from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.unsupported_dialect_error import (
    UnsupportedDialectError,
)
from takt.domain.model.target import Target
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.resolve_targets import resolve_targets

FULL_FILE = """\
name_template = "default {date}"

[targets.local]
url = "sqlite:///bench.sqlite"

[targets.maria_ci]
url = "mariadb+pymysql://user:pass@db.local:3306/bench"
"""

LOCAL = Target(name='local', url='sqlite:///bench.sqlite', dialect='sqlite')
MARIA_CI = Target(
    name='maria_ci',
    url='mariadb+pymysql://user:pass@db.local:3306/bench',
    dialect='mariadb',
)


def sources(
    tmp_path: Path,
    *,
    db_flags: tuple[str, ...] = (),
    target_flags: tuple[str, ...] = (),
    config_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> ConfigSources:
    return ConfigSources(
        db_flags=db_flags,
        target_flags=target_flags,
        config_path=config_path,
        name_flag=None,
        environ=environ or {},
        cwd=tmp_path,
    )


def sqlite_target(url: str) -> Target:
    return Target(name=None, url=url, dialect='sqlite')


@pytest.fixture
def with_toml(tmp_path: Path) -> Path:
    (tmp_path / 'takt.toml').write_text(FULL_FILE, encoding='utf-8')
    return tmp_path


def test_toml_level(with_toml: Path) -> None:
    assert resolve_targets(sources(with_toml)) == (LOCAL, MARIA_CI)


def test_env_replaces_toml(with_toml: Path) -> None:
    environ = {'TAKT_DB': 'sqlite:///a.sqlite  sqlite:///b.sqlite'}

    assert resolve_targets(sources(with_toml, environ=environ)) == (
        sqlite_target('sqlite:///a.sqlite'),
        sqlite_target('sqlite:///b.sqlite'),
    )


def test_blank_env_is_ignored(with_toml: Path) -> None:
    environ = {'TAKT_DB': '   '}

    assert resolve_targets(sources(with_toml, environ=environ)) == (
        LOCAL,
        MARIA_CI,
    )


def test_flags_replace_env_and_toml(with_toml: Path) -> None:
    resolved = resolve_targets(
        sources(
            with_toml,
            db_flags=('sqlite:///c.sqlite',),
            environ={'TAKT_DB': 'sqlite:///a.sqlite'},
        ),
    )

    assert resolved == (sqlite_target('sqlite:///c.sqlite'),)


def test_db_and_target_flags_union(with_toml: Path) -> None:
    resolved = resolve_targets(
        sources(
            with_toml,
            db_flags=('sqlite:///c.sqlite',),
            target_flags=('maria_ci',),
        ),
    )

    assert resolved == (sqlite_target('sqlite:///c.sqlite'), MARIA_CI)


def test_unknown_target(with_toml: Path) -> None:
    with pytest.raises(ConfigurationError) as error:
        resolve_targets(sources(with_toml, target_flags=('nope',)))

    assert str(error.value) == (
        "unknown target 'nope'; known targets: local, maria_ci"
    )


def test_unknown_target_without_toml(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError) as error:
        resolve_targets(sources(tmp_path, target_flags=('x',)))

    assert str(error.value) == "unknown target 'x'; known targets: none"


def test_duplicates_removed(tmp_path: Path) -> None:
    url = 'sqlite:///c.sqlite'

    resolved = resolve_targets(sources(tmp_path, db_flags=(url, url)))

    assert resolved == (sqlite_target(url),)


def test_no_targets_anywhere(tmp_path: Path) -> None:
    assert resolve_targets(sources(tmp_path)) == ()


def test_unsupported_url_in_toml(tmp_path: Path) -> None:
    (tmp_path / 'takt.toml').write_text(
        '[targets.pg]\nurl = "postgresql://u@h/db"\n',
        encoding='utf-8',
    )

    with pytest.raises(UnsupportedDialectError):
        resolve_targets(sources(tmp_path))


def test_explicit_config_path(tmp_path: Path) -> None:
    other = tmp_path / 'other.toml'
    other.write_text(FULL_FILE, encoding='utf-8')

    assert resolve_targets(sources(tmp_path, config_path=other)) == (
        LOCAL,
        MARIA_CI,
    )
