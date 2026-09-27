"""Alembic environment that runs on a connection passed by takt."""

from alembic import context

from takt.infrastructure.db.schema.tables import METADATA

if context.is_offline_mode():
    message = 'offline migrations are not supported'
    raise RuntimeError(message)

connection = context.config.attributes['connection']
"""Open connection that takt passes in the Alembic config."""

context.configure(
    connection=connection,
    target_metadata=METADATA,
    version_table='takt_alembic_version',
    render_as_batch=connection.dialect.name == 'sqlite',
)
with context.begin_transaction():
    context.run_migrations()
