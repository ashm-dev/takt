from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from takt.domain.errors.execution_error import ExecutionError
from takt.domain.model.target import Target
from takt.infrastructure.db.alembic_schema_migrator import (
    MIGRATIONS_DIRECTORY,
    AlembicSchemaMigrator,
)
from takt.infrastructure.db.engine_factory import create_target_engine
from takt.infrastructure.db.schema.tables import METADATA

VERSION_TABLE = 'takt_alembic_version'
EXPECTED_TABLES = frozenset(
    (
        'takt_suite',
        'takt_benchmark',
        'takt_worker_run',
        'takt_measurement',
        'takt_run_metadata',
        'takt_loaded_hash',
        VERSION_TABLE,
    ),
)


def read_versions(engine: sa.Engine) -> list[str]:
    with engine.connect() as connection:
        return list(
            connection.execute(
                sa.text('SELECT version_num FROM takt_alembic_version'),
            ).scalars(),
        )


def assert_upgraded(target: Target) -> None:
    engine = create_target_engine(target)
    table_names = set(sa.inspect(engine).get_table_names())
    assert table_names == EXPECTED_TABLES
    assert 'alembic_version' not in table_names
    assert read_versions(engine) == ['0001']


def schema_differences(target: Target) -> list[object]:
    engine = create_target_engine(target)
    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection,
            opts={'version_table': VERSION_TABLE, 'compare_type': True},
        )
        return list(compare_metadata(context, METADATA))


def add_conflicting_index(target: Target) -> None:
    with create_target_engine(target).begin() as connection:
        connection.exec_driver_sql('CREATE TABLE other (x INTEGER)')
        connection.exec_driver_sql(
            'CREATE INDEX ix_takt_suite_result_date ON other (x)',
        )


def test_head_returns_initial_revision_for_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    target = Target(name=None, url='sqlite:///unused.db', dialect='sqlite')

    assert AlembicSchemaMigrator().head(target) == '0001'
    assert not (tmp_path / 'unused.db').exists()


def test_head_returns_initial_revision_for_mariadb() -> None:
    target = Target(
        name=None,
        url='mariadb+pymysql://u:p@127.0.0.1:1/db',
        dialect='mariadb',
    )

    assert AlembicSchemaMigrator().head(target) == '0001'


def test_head_raises_for_dialect_without_migrations() -> None:
    target = Target(
        name=None,
        url='postgresql://u:p@127.0.0.1:1/db',
        dialect='postgresql',
    )

    with pytest.raises(
        ExecutionError,
        match='no migrations found for dialect postgresql',
    ):
        AlembicSchemaMigrator().head(target)


def test_head_raises_for_empty_versions_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / 'sqlite' / 'versions').mkdir(parents=True)
    monkeypatch.setattr(
        'takt.infrastructure.db.alembic_schema_migrator.MIGRATIONS_DIRECTORY',
        tmp_path,
    )
    target = Target(name=None, url='sqlite:///unused.db', dialect='sqlite')

    with pytest.raises(
        ExecutionError,
        match='no migrations found for dialect sqlite',
    ):
        AlembicSchemaMigrator().head(target)


def test_upgrade_creates_schema_on_sqlite(sqlite_target: Target) -> None:
    AlembicSchemaMigrator().upgrade(sqlite_target)

    assert_upgraded(sqlite_target)


def test_upgrade_twice_is_noop_on_sqlite(sqlite_target: Target) -> None:
    migrator = AlembicSchemaMigrator()

    migrator.upgrade(sqlite_target)
    migrator.upgrade(sqlite_target)

    assert_upgraded(sqlite_target)


def test_schema_matches_metadata_on_sqlite(sqlite_target: Target) -> None:
    AlembicSchemaMigrator().upgrade(sqlite_target)

    assert schema_differences(sqlite_target) == []


def test_upgrade_failure_raises_execution_error(sqlite_target: Target) -> None:
    add_conflicting_index(sqlite_target)

    with pytest.raises(ExecutionError) as migrate_error:
        AlembicSchemaMigrator().upgrade(sqlite_target)

    assert str(migrate_error.value) == (
        f'cannot migrate database {sqlite_target.display()}: '
        'index ix_takt_suite_result_date already exists'
    )
    assert isinstance(migrate_error.value.__cause__, sa.exc.OperationalError)


def test_failed_upgrade_leaves_no_takt_tables_on_sqlite(
    sqlite_target: Target,
) -> None:
    add_conflicting_index(sqlite_target)

    with pytest.raises(ExecutionError):
        AlembicSchemaMigrator().upgrade(sqlite_target)

    engine = create_target_engine(sqlite_target)
    assert sa.inspect(engine).get_table_names() == ['other']


@pytest.mark.mariadb
def test_upgrade_creates_schema_on_mariadb(mariadb_target: Target) -> None:
    AlembicSchemaMigrator().upgrade(mariadb_target)

    assert_upgraded(mariadb_target)


@pytest.mark.mariadb
def test_schema_matches_metadata_on_mariadb(mariadb_target: Target) -> None:
    AlembicSchemaMigrator().upgrade(mariadb_target)

    assert schema_differences(mariadb_target) == []


@pytest.mark.parametrize('dialect', ['sqlite', 'mariadb'])
def test_migration_files_do_not_import_runtime_schema(dialect: str) -> None:
    source = (
        MIGRATIONS_DIRECTORY / dialect / 'versions' / '0001_initial.py'
    ).read_text(encoding='utf-8')

    assert 'KNOWN_METADATA_KEYS' not in source
    assert 'schema.tables' not in source
