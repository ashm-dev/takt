"""Tables, keys and indexes that the takt schema must have."""

Columns = tuple[str, ...]
ForeignKey = tuple[Columns, str, Columns]

RUN_KEY: Columns = ('suite_hash', 'benchmark_position', 'run_position')
BENCHMARK_KEY: Columns = ('suite_hash', 'benchmark_position')

PRIMARY_KEYS: tuple[tuple[str, Columns], ...] = (
    ('takt_suite', ('hash',)),
    ('takt_benchmark', BENCHMARK_KEY),
    ('takt_worker_run', RUN_KEY),
    ('takt_measurement', (*RUN_KEY, 'kind', 'position')),
    ('takt_run_metadata', RUN_KEY),
    ('takt_loaded_hash', ('hash',)),
)

FOREIGN_KEYS: tuple[tuple[str, ForeignKey], ...] = (
    ('takt_benchmark', (('suite_hash',), 'takt_suite', ('hash',))),
    ('takt_worker_run', (BENCHMARK_KEY, 'takt_benchmark', BENCHMARK_KEY)),
    ('takt_measurement', (RUN_KEY, 'takt_worker_run', RUN_KEY)),
    ('takt_run_metadata', (RUN_KEY, 'takt_worker_run', RUN_KEY)),
)

TABLE_NAMES = frozenset(table_name for table_name, _ in PRIMARY_KEYS)
INDEX_NAMES = frozenset(('ix_takt_suite_name', 'ix_takt_suite_result_date'))
