"""Insertion of a whole suite into the takt tables."""

from datetime import UTC

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from takt.domain.model.metadata_key_types import METADATA_KEY_TYPES
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.suite import Suite
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.worker_run import WorkerRun
from takt.infrastructure.db.schema.tables import (
    BENCHMARK_TABLE,
    LOADED_HASH_TABLE,
    MEASUREMENT_TABLE,
    RUN_METADATA_TABLE,
    SUITE_TABLE,
    WORKER_RUN_TABLE,
)

_Row = dict[str, object]
"""Column values of one inserted row."""


def insert_suite(connection: Connection, record: SuiteRecord) -> None:
    """Insert every row of a suite without committing.

    :param connection: Connection with an open transaction.
    :param record: Suite with storage attributes.
    """
    suite = record.suite
    keyed_runs = _keyed_runs(suite)
    _insert(connection, SUITE_TABLE, [_suite_row(record)])
    _insert(connection, BENCHMARK_TABLE, _benchmark_rows(suite))
    _insert(connection, WORKER_RUN_TABLE, [key for key, _run in keyed_runs])
    _insert(
        connection,
        MEASUREMENT_TABLE,
        [
            measurement_row
            for key, run in keyed_runs
            for measurement_row in _measurement_rows(key, run)
        ],
    )
    _insert(
        connection,
        RUN_METADATA_TABLE,
        [key | _metadata_columns(run.metadata) for key, run in keyed_runs],
    )
    _insert(connection, LOADED_HASH_TABLE, [{'hash': suite.hash}])


def _insert(connection: Connection, table: sa.Table, rows: list[_Row]) -> None:
    # An empty executemany would insert one row of default values.
    if rows:
        connection.execute(table.insert(), rows)


def _suite_row(record: SuiteRecord) -> _Row:
    return {
        'hash': record.suite.hash,
        'name': record.name,
        'format_version': record.suite.format_version,
        'source': record.source.value,
        'result_date': record.suite.result_date,
        'loaded_at': record.loaded_at.astimezone(UTC).replace(tzinfo=None),
    }


def _benchmark_rows(suite: Suite) -> list[_Row]:
    return [
        {
            'suite_hash': suite.hash,
            'benchmark_position': benchmark_position,
            'name': benchmark.name,
        }
        for benchmark_position, benchmark in enumerate(suite.benchmarks)
    ]


def _keyed_runs(suite: Suite) -> list[tuple[_Row, WorkerRun]]:
    return [
        (
            {
                'suite_hash': suite.hash,
                'benchmark_position': benchmark_position,
                'run_position': run_position,
            },
            run,
        )
        for benchmark_position, benchmark in enumerate(suite.benchmarks)
        for run_position, run in enumerate(benchmark.runs)
    ]


def _measurement_rows(key: _Row, run: WorkerRun) -> list[_Row]:
    return [
        key
        | {
            'kind': measurement.kind.value,
            'position': position,
            'loops': measurement.loops,
            'value': measurement.value,
        }
        for collection in (run.warmups, run.values)
        for position, measurement in enumerate(collection)
    ]


def _metadata_columns(metadata: RunMetadata) -> _Row:
    columns: _Row = {key: getattr(metadata, key) for key in METADATA_KEY_TYPES}
    # A plain None in a JSON column is stored as the JSON literal null.
    columns.update(
        (key, sa.null())
        for key, key_type in METADATA_KEY_TYPES.items()
        if key_type is tuple and columns[key] is None
    )
    custom = {
        key: list(element) if isinstance(element, tuple) else element
        for key, element in metadata.custom.items()
    }
    columns['custom'] = custom or sa.null()
    return columns
