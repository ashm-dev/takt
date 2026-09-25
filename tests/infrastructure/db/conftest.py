from collections.abc import Iterator

import pytest
import sqlalchemy as sa

from takt.domain.model.target import Target
from takt.infrastructure.db.alembic_schema_migrator import AlembicSchemaMigrator
from takt.infrastructure.db.engine_factory import create_target_engine


@pytest.fixture(
    params=[
        'sqlite_target',
        pytest.param('mariadb_target', marks=pytest.mark.mariadb),
    ],
)
def target(request: pytest.FixtureRequest) -> Target:
    migrated: Target = request.getfixturevalue(request.param)
    AlembicSchemaMigrator().upgrade(migrated)
    return migrated


@pytest.fixture
def engine(target: Target) -> Iterator[sa.Engine]:
    target_engine = create_target_engine(target)
    yield target_engine
    target_engine.dispose()
