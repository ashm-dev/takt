import pytest

from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.worker_run import WorkerRun

WARMUP = Measurement(kind=MeasurementKind.WARMUP, value=0.1, loops=1)
VALUE = Measurement(kind=MeasurementKind.VALUE, value=0.2, loops=None)


@pytest.mark.parametrize(
    ('warmups', 'values'),
    [((WARMUP,), (VALUE,)), ((WARMUP,), ()), ((), (VALUE,))],
)
def test_worker_run_accepts_valid_measurements(
    warmups: tuple[Measurement, ...],
    values: tuple[Measurement, ...],
) -> None:
    run = WorkerRun(metadata=RunMetadata(), warmups=warmups, values=values)

    assert run.warmups == warmups
    assert run.values == values


def test_worker_run_rejects_value_in_warmups() -> None:
    with pytest.raises(
        ValueError,
        match='warmups must contain only warmup measurements',
    ):
        WorkerRun(metadata=RunMetadata(), warmups=(VALUE,), values=())


def test_worker_run_rejects_warmup_in_values() -> None:
    with pytest.raises(
        ValueError,
        match='values must contain only value measurements',
    ):
        WorkerRun(metadata=RunMetadata(), warmups=(), values=(WARMUP,))


def test_worker_run_rejects_empty_run() -> None:
    with pytest.raises(
        ValueError, match='worker run must have warmups or values'
    ):
        WorkerRun(metadata=RunMetadata(), warmups=(), values=())
