"""Tables, keys and indexes that the takt schema must have."""

Columns = tuple[str, ...]
"""Ordered column names of a key."""

ForeignKey = tuple[Columns, str, Columns]
"""Local columns, referred table and referred columns of a foreign key."""

RUN_KEY: Columns = ('suite_hash', 'benchmark_position', 'run_position')
"""Primary key of ``takt_worker_run`` and of the tables that refer to it."""

BENCHMARK_KEY: Columns = ('suite_hash', 'benchmark_position')
"""Primary key of ``takt_benchmark``."""

PRIMARY_KEYS: tuple[tuple[str, Columns], ...] = (
    ('takt_suite', ('hash',)),
    ('takt_benchmark', BENCHMARK_KEY),
    ('takt_worker_run', RUN_KEY),
    ('takt_measurement', (*RUN_KEY, 'kind', 'position')),
    ('takt_run_metadata', RUN_KEY),
    ('takt_loaded_hash', ('hash',)),
)
"""Primary key columns of every takt table."""

FOREIGN_KEYS: tuple[tuple[str, ForeignKey], ...] = (
    ('takt_benchmark', (('suite_hash',), 'takt_suite', ('hash',))),
    ('takt_worker_run', (BENCHMARK_KEY, 'takt_benchmark', BENCHMARK_KEY)),
    ('takt_measurement', (RUN_KEY, 'takt_worker_run', RUN_KEY)),
    ('takt_run_metadata', (RUN_KEY, 'takt_worker_run', RUN_KEY)),
)
"""Foreign key of every takt table that has one."""

TABLE_NAMES = frozenset(table_name for table_name, _ in PRIMARY_KEYS)
"""Names of all takt tables."""

INDEX_NAMES = frozenset(('ix_takt_suite_name', 'ix_takt_suite_result_date'))
"""Names of the indexes on ``takt_suite``."""
