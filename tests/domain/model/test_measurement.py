import dataclasses

import pytest

from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind


def test_value_measurement_keeps_fields() -> None:
    measurement = Measurement(
        kind=MeasurementKind.VALUE,
        value=0.5,
        loops=None,
    )

    assert measurement.kind is MeasurementKind.VALUE
    assert measurement.value == 0.5
    assert measurement.loops is None


def test_value_measurement_rejects_loops() -> None:
    with pytest.raises(
        ValueError, match='value measurement must not have loops'
    ):
        Measurement(kind=MeasurementKind.VALUE, value=0.5, loops=1)


@pytest.mark.parametrize('value', [0.0, -1.0])
def test_value_measurement_rejects_non_positive_value(value: float) -> None:
    with pytest.raises(ValueError, match='value must be a finite number > 0'):
        Measurement(kind=MeasurementKind.VALUE, value=value, loops=None)


def test_warmup_measurement_keeps_fields() -> None:
    measurement = Measurement(
        kind=MeasurementKind.WARMUP,
        value=0.0,
        loops=3,
    )

    assert measurement.loops == 3
    assert measurement.value == 0.0


@pytest.mark.parametrize('loops', [None, 0])
def test_warmup_measurement_requires_positive_loops(loops: int | None) -> None:
    with pytest.raises(ValueError, match='warmup loops must be >= 1'):
        Measurement(kind=MeasurementKind.WARMUP, value=0.1, loops=loops)


def test_warmup_measurement_rejects_negative_value() -> None:
    with pytest.raises(
        ValueError, match='warmup value must be a finite number >= 0'
    ):
        Measurement(kind=MeasurementKind.WARMUP, value=-0.1, loops=1)


def test_measurement_is_frozen() -> None:
    measurement = Measurement(
        kind=MeasurementKind.VALUE,
        value=0.5,
        loops=None,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        measurement.value = 1.0  # type: ignore[misc]
