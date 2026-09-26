"""Single measured or warmup value."""

import math
from dataclasses import dataclass

from takt.domain.model.measurement_kind import MeasurementKind


@dataclass(frozen=True, kw_only=True)
class Measurement:
    """Single value of a worker run.

    :ivar kind: Measured value or warmup.
    :ivar value: Value per loop iteration.
    :ivar loops: Loop count, set only for warmups.
    """

    kind: MeasurementKind
    value: float
    loops: int | None

    def __post_init__(self) -> None:
        """Validate the measurement invariants.

        :raises ValueError: If an invariant is broken.
        """
        if self.kind is MeasurementKind.VALUE:
            self._validate_value()
        else:
            self._validate_warmup()

    def _validate_value(self) -> None:
        if self.loops is not None:
            msg = 'value measurement must not have loops'
            raise ValueError(msg)
        if not (math.isfinite(self.value) and self.value > 0):
            msg = 'value must be a finite number > 0'
            raise ValueError(msg)

    def _validate_warmup(self) -> None:
        if self.loops is None or self.loops < 1:
            msg = 'warmup loops must be >= 1'
            raise ValueError(msg)
        if not (math.isfinite(self.value) and self.value >= 0):
            msg = 'warmup value must be a finite number >= 0'
            raise ValueError(msg)
