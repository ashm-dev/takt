from dataclasses import replace
from pathlib import Path

import pytest

from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.unsupported_dialect_error import (
    UnsupportedDialectError,
)
from takt.domain.model.target import Target
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.resolve_targets import resolve_targets
from tests.domain.exact_pattern import exact_pattern
from tests.infrastructure.config.config_inputs import FULL_FILE, sources

UNSUPPORTED_POSTGRESQL = (
    "unsupported database 'postgresql'; "
    'supported in this version: mariadb, sqlite'
)
"""Error text for a PostgreSQL URL, which this version does not support."""

LOCAL = Target(name='local', url='sqlite:///bench.sqlite', dialect='sqlite')
"""Target that ``FULL_FILE`` defines as ``local``."""

MARIA_CI = Target(
    name='maria_ci',
    url='mariadb+pymysql://user:pass@db.local:3306/bench',
    dialect='mariadb',
)
"""Target that ``FULL_FILE`` defines as ``maria_ci``."""


def sqlite_target(url: str) -> Target:
    return Target(name=None, url=url, dialect='sqlite')


@pytest.fixture
def with_toml(tmp_path: Path) -> Path:
    (tmp_path / 'takt.toml').write_text(FULL_FILE, encoding='utf-8')
    return tmp_path


@pytest.fixture
def bare_sources(tmp_path: Path) -> ConfigSources:
    return sources(tmp_path)


def test_toml_level(with_toml: Path) -> None:
    assert resolve_targets(sources(with_toml)) == (LOCAL, MARIA_CI)


def test_env_replaces_toml(with_toml: Path) -> None:
    environ = {'TAKT_DB': 'sqlite:///a.sqlite  sqlite:///b.sqlite'}

    assert resolve_targets(replace(sources(with_toml), environ=environ)) == (
        sqlite_target('sqlite:///a.sqlite'),
        sqlite_target('sqlite:///b.sqlite'),
    )


def test_blank_env_is_ignored(with_toml: Path) -> None:
    environ = {'TAKT_DB': '   '}

    assert resolve_targets(replace(sources(with_toml), environ=environ)) == (
        LOCAL,
        MARIA_CI,
    )


def test_flags_replace_env_and_toml(with_toml: Path) -> None:
    resolved = resolve_targets(
        replace(
            sources(with_toml),
            db_flags=('sqlite:///c.sqlite',),
            environ={'TAKT_DB': 'sqlite:///a.sqlite'},
        ),
    )

    assert resolved == (sqlite_target('sqlite:///c.sqlite'),)


def test_db_and_target_flags_union(with_toml: Path) -> None:
    resolved = resolve_targets(
        replace(
            sources(with_toml),
            db_flags=('sqlite:///c.sqlite',),
            target_flags=('maria_ci',),
        ),
    )

    assert resolved == (sqlite_target('sqlite:///c.sqlite'), MARIA_CI)


def test_unknown_target(with_toml: Path) -> None:
    with pytest.raises(ConfigurationError) as error:
        resolve_targets(replace(sources(with_toml), target_flags=('nope',)))

    assert str(error.value) == (
        "unknown target 'nope'; known targets: local, maria_ci"
    )


def test_unknown_target_without_toml(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError) as error:
        resolve_targets(replace(sources(tmp_path), target_flags=('x',)))

    assert str(error.value) == (
        f"unknown target 'x': no takt.toml in {tmp_path}; use --config PATH"
    )


def test_unknown_target_with_empty_toml(bare_sources: ConfigSources) -> None:
    (bare_sources.cwd / 'takt.toml').write_text('', encoding='utf-8')

    with pytest.raises(
        ConfigurationError,
        match=exact_pattern("unknown target 'x'; known targets: none"),
    ):
        resolve_targets(replace(bare_sources, target_flags=('x',)))


def test_duplicates_removed(tmp_path: Path) -> None:
    url = 'sqlite:///c.sqlite'

    resolved = resolve_targets(replace(sources(tmp_path), db_flags=(url, url)))

    assert resolved == (sqlite_target(url),)


def test_one_sqlite_file_in_several_spellings(tmp_path: Path) -> None:
    spellings = (
        'sqlite:///c.sqlite',
        f'sqlite:///{tmp_path}/c.sqlite',
        'sqlite+pysqlite:///./sub/../c.sqlite',
        'sqlite:///file:c.sqlite?uri=true',
    )

    resolved = resolve_targets(
        replace(sources(tmp_path), db_flags=spellings),
    )

    assert resolved == (sqlite_target('sqlite:///c.sqlite'),)


def test_one_mariadb_database_in_several_spellings(with_toml: Path) -> None:
    same_database = 'mariadb://other:secret@db.local/bench'
    other_port = 'mariadb+pymysql://user:pass@db.local:3307/bench'

    resolved = resolve_targets(
        replace(
            sources(with_toml),
            db_flags=(same_database, other_port),
            target_flags=('maria_ci',),
        ),
    )

    assert resolved == (
        Target(name=None, url=same_database, dialect='mariadb'),
        Target(name=None, url=other_port, dialect='mariadb'),
    )


def test_first_config_name_kept_for_same_file(tmp_path: Path) -> None:
    (tmp_path / 'takt.toml').write_text(
        '[targets.one]\nurl = "sqlite:///bench.sqlite"\n'
        '[targets.two]\nurl = "sqlite:///./bench.sqlite"\n',
        encoding='utf-8',
    )

    resolved = resolve_targets(sources(tmp_path))

    assert resolved == (
        Target(name='one', url='sqlite:///bench.sqlite', dialect='sqlite'),
    )


def test_no_targets_anywhere(tmp_path: Path) -> None:
    assert resolve_targets(sources(tmp_path)) == ()


def test_unsupported_url_in_toml(bare_sources: ConfigSources) -> None:
    config = bare_sources.cwd / 'takt.toml'
    config.write_text(
        '[targets.pg]\nurl = "postgresql://u@h/db"\n',
        encoding='utf-8',
    )
    message = f"{config}: target 'pg': {UNSUPPORTED_POSTGRESQL}"

    with pytest.raises(UnsupportedDialectError, match=exact_pattern(message)):
        resolve_targets(bare_sources)


def test_unsupported_url_in_env(bare_sources: ConfigSources) -> None:
    environ = {'TAKT_DB': 'sqlite:///ok.sqlite postgresql://u:p@h/db'}
    message = f'TAKT_DB: {UNSUPPORTED_POSTGRESQL}'

    with pytest.raises(UnsupportedDialectError, match=exact_pattern(message)):
        resolve_targets(replace(bare_sources, environ=environ))


def test_unsupported_url_in_flag_has_no_source(
    bare_sources: ConfigSources,
) -> None:
    flags = ('postgresql://u@h/db',)

    with pytest.raises(
        UnsupportedDialectError,
        match=exact_pattern(UNSUPPORTED_POSTGRESQL),
    ):
        resolve_targets(replace(bare_sources, db_flags=flags))


def test_explicit_config_path(tmp_path: Path) -> None:
    other = tmp_path / 'other.toml'
    other.write_text(FULL_FILE, encoding='utf-8')

    assert resolve_targets(replace(sources(tmp_path), config_path=other)) == (
        LOCAL,
        MARIA_CI,
    )
