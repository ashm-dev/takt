from datetime import UTC, datetime

from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.suite import Suite
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.worker_run import WorkerRun


def test_suite_record_keeps_fields() -> None:
    run = WorkerRun(
        metadata=RunMetadata(),
        warmups=(),
        values=(
            Measurement(kind=MeasurementKind.VALUE, value=0.2, loops=None),
        ),
    )
    suite = Suite(
        hash='b' * 64,
        format_version='1.0',
        result_date=None,
        benchmarks=(Benchmark(name='nbody', runs=(run,)),),
    )
    loaded_at = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    record = SuiteRecord(
        suite=suite,
        name=None,
        source=SuiteSource.IMPORT,
        loaded_at=loaded_at,
    )

    assert record.suite is suite
    assert record.name is None
    assert record.source is SuiteSource.IMPORT
    assert record.loaded_at == loaded_at
