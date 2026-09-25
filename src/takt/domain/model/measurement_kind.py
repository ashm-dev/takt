"""Kind of a measurement."""

from enum import StrEnum


class MeasurementKind(StrEnum):
    """Kind of a measurement inside a worker run."""

    VALUE = 'value'
    WARMUP = 'warmup'
