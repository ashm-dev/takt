import pytest

from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.suite import Suite
from takt.domain.model.worker_run import WorkerRun

RUN = WorkerRun(
    metadata=RunMetadata(),
    warmups=(),
    values=(Measurement(kind=MeasurementKind.VALUE, value=0.2, loops=None),),
)
NBODY = Benchmark(name='nbody', runs=(RUN,))
VALID_HASH = 'a' * 64
BAD_HASHES = (
    'A' * 64,
    'a' * 63,
    'g' * 64,
    '',
)


def test_suite_keeps_fields() -> None:
    suite = Suite(
        hash=VALID_HASH,
        format_version='1.0',
        result_date=None,
        benchmarks=(NBODY,),
    )

    assert suite.hash == VALID_HASH
    assert suite.benchmarks == (NBODY,)


@pytest.mark.parametrize('bad_hash', BAD_HASHES)
def test_suite_rejects_bad_hash(bad_hash: str) -> None:
    with pytest.raises(
        ValueError,
        match='suite hash must be 64 lowercase hex characters',
    ):
        Suite(
            hash=bad_hash,
            format_version='1.0',
            result_date=None,
            benchmarks=(NBODY,),
        )


def test_suite_rejects_empty_benchmarks() -> None:
    with pytest.raises(
        ValueError, match='suite must have at least one benchmark'
    ):
        Suite(
            hash=VALID_HASH,
            format_version='1.0',
            result_date=None,
            benchmarks=(),
        )


def test_suite_rejects_duplicate_benchmark_names() -> None:
    with pytest.raises(ValueError, match='benchmark names must be unique'):
        Suite(
            hash=VALID_HASH,
            format_version='1.0',
            result_date=None,
            benchmarks=(NBODY, NBODY),
        )
