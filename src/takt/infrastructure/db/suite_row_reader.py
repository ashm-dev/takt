"""Reading of a whole suite from the takt tables."""

import copy
import json
from datetime import UTC
from typing import Final

import sqlalchemy as sa
from sqlalchemy.engine import Connection, RowMapping

from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.metadata_key_types import METADATA_KEY_TYPES
from takt.domain.model.metadata_value import MetadataValue
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.suite import Suite
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.worker_run import WorkerRun
from takt.infrastructure.db.schema.tables import (
    BENCHMARK_TABLE,
    MEASUREMENT_TABLE,
    RUN_METADATA_TABLE,
    SUITE_TABLE,
    WORKER_RUN_TABLE,
)

_RunKey = tuple[int, int]
_MeasurementKey = tuple[int, int, str]
_BENCHMARK_POSITION: Final = 'benchmark_position'
_RUN: Final = (_BENCHMARK_POSITION, 'run_position')


def read_suite(connection: Connection, suite_hash: str) -> SuiteRecord | None:
    """Read a whole suite by its hash.

    :param connection: Open connection.
    :param suite_hash: Suite hash.
    :returns: The stored suite or ``None`` when it is missing.
    """
    suite_row = connection.execute(
        sa.select(SUITE_TABLE).where(SUITE_TABLE.c.hash == suite_hash),
    ).first()
    if suite_row is None:
        return None
    return SuiteRecord(
        suite=Suite(
            hash=suite_row.hash,
            format_version=suite_row.format_version,
            result_date=suite_row.result_date,
            benchmarks=_read_benchmarks(connection, suite_hash),
        ),
        name=suite_row.name,
        source=SuiteSource(suite_row.source),
        loaded_at=suite_row.loaded_at.replace(tzinfo=UTC),
    )


def _select_rows(
    connection: Connection,
    table: sa.Table,
    suite_hash: str,
    *order: str,
) -> sa.Result[*tuple[object, ...]]:
    return connection.execute(
        sa.select(table)
        .where(table.c.suite_hash == suite_hash)
        .order_by(*(table.c[column] for column in order)),
    )


def _read_benchmarks(
    connection: Connection,
    suite_hash: str,
) -> tuple[Benchmark, ...]:
    benchmark_rows = _select_rows(
        connection,
        BENCHMARK_TABLE,
        suite_hash,
        _BENCHMARK_POSITION,
    ).all()
    runs = _read_runs(connection, suite_hash)
    return tuple(
        Benchmark(
            name=benchmark_row.name,
            runs=tuple(runs[benchmark_row.benchmark_position]),
        )
        for benchmark_row in benchmark_rows
    )


def _read_runs(
    connection: Connection,
    suite_hash: str,
) -> dict[int, list[WorkerRun]]:
    measurements = _read_measurements(connection, suite_hash)
    metadata = _read_metadata(connection, suite_hash)
    runs: dict[int, list[WorkerRun]] = {}
    for run_row in _select_rows(
        connection, WORKER_RUN_TABLE, suite_hash, *_RUN
    ):
        run_key: _RunKey = (run_row.benchmark_position, run_row.run_position)
        runs.setdefault(run_key[0], []).append(
            WorkerRun(
                metadata=metadata[run_key],
                warmups=tuple(measurements.get((*run_key, 'warmup'), ())),
                values=tuple(measurements.get((*run_key, 'value'), ())),
            ),
        )
    return runs


def _read_measurements(
    connection: Connection,
    suite_hash: str,
) -> dict[_MeasurementKey, list[Measurement]]:
    measurements: dict[_MeasurementKey, list[Measurement]] = {}
    for row in _select_rows(
        connection,
        MEASUREMENT_TABLE,
        suite_hash,
        *_RUN,
        'kind',
        'position',
    ):
        measurement_key: _MeasurementKey = (
            row.benchmark_position,
            row.run_position,
            row.kind,
        )
        measurements.setdefault(measurement_key, []).append(
            Measurement(
                kind=MeasurementKind(row.kind),
                value=row.value,
                loops=row.loops,
            ),
        )
    return measurements


def _read_metadata(
    connection: Connection,
    suite_hash: str,
) -> dict[_RunKey, RunMetadata]:
    rows = _select_rows(connection, RUN_METADATA_TABLE, suite_hash, *_RUN)
    return {
        (row[_BENCHMARK_POSITION], row['run_position']): _to_metadata(row)
        for row in rows.mappings()
    }


def _to_metadata(row: RowMapping) -> RunMetadata:
    fields: dict[str, MetadataValue] = {}
    for key, key_type in METADATA_KEY_TYPES.items():
        column_value = _decoded(row[key]) if key_type is tuple else row[key]
        if isinstance(column_value, list):
            fields[key] = _string_tuple(column_value)
        elif isinstance(column_value, (int, float, str)):
            fields[key] = column_value
    return copy.replace(
        RunMetadata(custom=_to_custom(_decoded(row['custom']))),
        **fields,
    )


def _to_custom(custom_column: object) -> dict[str, MetadataValue]:
    if not isinstance(custom_column, dict):
        return {}
    return {
        str(custom_key): (
            _string_tuple(element) if isinstance(element, list) else element
        )
        for custom_key, element in custom_column.items()
    }


def _decoded(column_value: object) -> object:
    # MariaDB may return a JSON column as text when the driver leaves it raw.
    if isinstance(column_value, str):
        return json.loads(column_value)
    return column_value


def _string_tuple(elements: list[object]) -> tuple[str, ...]:
    return tuple(str(element) for element in elements)
