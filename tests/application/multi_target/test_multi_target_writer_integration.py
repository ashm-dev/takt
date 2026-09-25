from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

from takt.application.multi_target.multi_target_writer import MultiTargetWriter
from takt.application.multi_target.target_status import TargetStatus
from takt.application.multi_target.write_report import WriteReport
from takt.domain.model.target import Target
from takt.infrastructure.cache.file_schema_version_cache import (
    FileSchemaVersionCache,
)
from takt.infrastructure.db.alembic_schema_migrator import AlembicSchemaMigrator
from takt.infrastructure.db.sqlalchemy_target_connector import (
    SqlAlchemyTargetConnector,
)
from tests.infrastructure.db.suite_factory import make_record


def statuses(report: WriteReport) -> tuple[TargetStatus, ...]:
    return tuple(outcome.status for outcome in report.outcomes)


def sqlite_path(target: Target) -> Path:
    database = make_url(target.url).database
    assert database is not None
    return Path(database)


@pytest.mark.mariadb
def test_real_targets_all_or_nothing(
    tmp_path: Path,
    sqlite_target: Target,
    mariadb_target: Target,
) -> None:
    writer = MultiTargetWriter(
        connector=SqlAlchemyTargetConnector(),
        migrator=AlembicSchemaMigrator(),
        cache=FileSchemaVersionCache(file_path=tmp_path / 'cache.json'),
    )
    targets = (sqlite_target, mariadb_target)

    first = writer.write(make_record(), targets)
    second = writer.write(make_record(), targets)
    sqlite_path(sqlite_target).unlink()
    third = writer.write(make_record(), targets)

    assert statuses(first) == (TargetStatus.WRITTEN, TargetStatus.WRITTEN)
    assert statuses(second) == (
        TargetStatus.ALREADY_LOADED,
        TargetStatus.ALREADY_LOADED,
    )
    assert [outcome.existing_name for outcome in second.outcomes] == [
        'default',
        'default',
    ]
    assert statuses(third) == (
        TargetStatus.WRITTEN,
        TargetStatus.ALREADY_LOADED,
    )
