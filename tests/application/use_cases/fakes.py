from datetime import datetime
from pathlib import Path

from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.suite import Suite
from takt.domain.model.worker_run import WorkerRun

DEFAULT_HASH = 'f' * 64


class FakeReader:
    def __init__(
        self,
        suite: Suite | None = None,
        error: Exception | None = None,
    ) -> None:
        self.suite = suite
        self.error = error
        self.calls: list[Path] = []

    def read(self, path: Path) -> Suite:
        self.calls.append(path)
        if self.error is not None:
            raise self.error
        assert self.suite is not None
        return self.suite


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self.moment = moment
        self.calls = 0

    def now(self) -> datetime:
        self.calls += 1
        return self.moment


def make_suite(
    python_version: str | None = '3.14.0',
    hostname: str | None = 'bench-host',
) -> Suite:
    run = WorkerRun(
        metadata=RunMetadata(python_version=python_version, hostname=hostname),
        warmups=(),
        values=(
            Measurement(kind=MeasurementKind.VALUE, value=0.1, loops=None),
        ),
    )
    return Suite(
        hash=DEFAULT_HASH,
        format_version='1.0',
        result_date=None,
        benchmarks=(Benchmark(name='nbody', runs=(run,)),),
    )
