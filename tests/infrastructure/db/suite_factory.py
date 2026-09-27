from datetime import UTC, datetime

from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.suite import Suite
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.worker_run import WorkerRun

DEFAULT_HASH = 'a' * 64
"""Suite hash that ``make_record`` uses by default."""

DEFAULT_RESULT_DATE = datetime.fromisoformat('2026-09-25T10:00:00.123456')
"""Default result date of ``make_record``, with microseconds to keep."""

LOADED_AT = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)
"""Time when the test record was loaded into the database."""


def warmup(loops: int, value: float) -> Measurement:
    return Measurement(kind=MeasurementKind.WARMUP, value=value, loops=loops)


def value(measured: float) -> Measurement:
    return Measurement(kind=MeasurementKind.VALUE, value=measured, loops=None)


def make_record(
    *,
    suite_hash: str = DEFAULT_HASH,
    name: str | None = 'default',
    result_date: datetime | None = DEFAULT_RESULT_DATE,
    first_warmup_loops: int = 1,
) -> SuiteRecord:
    nbody = Benchmark(
        name='nbody',
        runs=(
            WorkerRun(
                metadata=RunMetadata(calibrate_loops=2),
                warmups=(warmup(first_warmup_loops, 0.5), warmup(2, 0.25)),
                values=(),
            ),
            WorkerRun(
                metadata=RunMetadata(
                    name='nbody',
                    unit='second',
                    loops=2,
                    python_version='3.14.0 (64-bit)',
                    hostname='bench-host',
                    cpu_count=8,
                    duration=1.5,
                    tags=('apps', 'math'),
                    python_hash_seed='0',
                    custom={
                        'compiler_flags': '-O3',
                        'run_id': 7,
                        'ratio': 0.5,
                        'labels': ('a', 'b'),
                    },
                ),
                warmups=(warmup(2, 0.2),),
                values=(value(0.21), value(0.22), value(0.23)),
            ),
        ),
    )
    json_dumps = Benchmark(
        name='json_dumps',
        runs=(
            WorkerRun(
                metadata=RunMetadata(),
                warmups=(),
                values=(value(0.001),),
            ),
        ),
    )
    return SuiteRecord(
        suite=Suite(
            hash=suite_hash,
            format_version='1.0',
            result_date=result_date,
            benchmarks=(nbody, json_dumps),
        ),
        name=name,
        source=SuiteSource.IMPORT,
        loaded_at=LOADED_AT,
    )
