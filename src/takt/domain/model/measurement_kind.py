"""Kind of a measurement."""

from enum import StrEnum


class MeasurementKind(StrEnum):
    """Kind of a measurement inside a worker run."""

    VALUE = 'value'
    """Measured value that goes into the results."""

    WARMUP = 'warmup'
    """Warmup value that is kept but not used in comparisons."""
