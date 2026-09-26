"""Schema migrator backed by Alembic."""

import contextlib
from pathlib import Path
from typing import Final

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from takt.domain.errors.execution_error import ExecutionError
from takt.domain.model.target import Target
from takt.infrastructure.db.database_error import database_error
from takt.infrastructure.db.migration_engine_factory import (
    create_migration_engine,
)

MIGRATIONS_DIRECTORY: Final = Path(__file__).parent / 'migrations'


class AlembicSchemaMigrator:
    """Apply takt schema migrations with Alembic."""

    def head(self, target: Target) -> str:
        """Return the latest revision for the target dialect.

        :param target: Target database; it is not contacted.
        :returns: Head revision identifier.
        :raises ExecutionError: If the dialect has no migrations.
        """
        missing = ExecutionError(
            f'no migrations found for dialect {target.dialect}',
        )
        if not _versions_directory(target).is_dir():
            raise missing
        revision = ScriptDirectory.from_config(
            _alembic_config(target),
        ).get_current_head()
        if revision is None:
            raise missing
        return revision

    def upgrade(self, target: Target) -> None:
        """Bring the target database to the head revision.

        :param target: Target database.
        :raises ExecutionError: If the migration fails.
        """
        try:
            _upgrade(target)
        except Exception as error:
            message = f'cannot migrate database {target.display()}'
            raise database_error(message, error) from error


def _upgrade(target: Target) -> None:
    config = _alembic_config(target)
    engine = create_migration_engine(target)
    with contextlib.ExitStack() as cleanup:
        cleanup.callback(engine.dispose)
        config.attributes['connection'] = cleanup.enter_context(engine.begin())
        command.upgrade(config, 'head')


def _versions_directory(target: Target) -> Path:
    return MIGRATIONS_DIRECTORY / target.dialect / 'versions'


def _alembic_config(target: Target) -> Config:
    config = Config()
    config.set_main_option('script_location', str(MIGRATIONS_DIRECTORY))
    config.set_main_option(
        'version_locations',
        str(_versions_directory(target)),
    )
    config.set_main_option('path_separator', 'os')
    return config
