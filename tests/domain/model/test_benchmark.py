import pytest

from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.worker_run import WorkerRun

RUN = WorkerRun(
    metadata=RunMetadata(),
    warmups=(),
    values=(Measurement(kind=MeasurementKind.VALUE, value=0.2, loops=None),),
)
"""Valid worker run with one value."""


def test_benchmark_keeps_fields() -> None:
    benchmark = Benchmark(name='nbody', runs=(RUN,))

    assert benchmark.name == 'nbody'
    assert benchmark.runs == (RUN,)


def test_benchmark_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match='benchmark name must not be empty'):
        Benchmark(name='', runs=(RUN,))


def test_benchmark_rejects_empty_runs() -> None:
    with pytest.raises(
        ValueError, match='benchmark must have at least one run'
    ):
        Benchmark(name='nbody', runs=())
