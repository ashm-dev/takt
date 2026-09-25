"""One pyperf worker process run."""

from dataclasses import dataclass

from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata


@dataclass(frozen=True, kw_only=True)
class WorkerRun:
    """One pyperf worker run.

    :ivar metadata: Full metadata of the run.
    :ivar warmups: Warmup measurements in file order.
    :ivar values: Value measurements in file order.
    """

    metadata: RunMetadata
    warmups: tuple[Measurement, ...]
    values: tuple[Measurement, ...]

    def __post_init__(self) -> None:
        """Validate the worker run invariants.

        :raises ValueError: If an invariant is broken.
        """
        warmup_kinds = {warmup.kind for warmup in self.warmups}
        if warmup_kinds - {MeasurementKind.WARMUP}:
            msg = 'warmups must contain only warmup measurements'
            raise ValueError(msg)
        value_kinds = {measurement.kind for measurement in self.values}
        if value_kinds - {MeasurementKind.VALUE}:
            msg = 'values must contain only value measurements'
            raise ValueError(msg)
        if not self.warmups and not self.values:
            msg = 'worker run must have warmups or values'
            raise ValueError(msg)
