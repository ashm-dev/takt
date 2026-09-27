"""Single benchmark inside a suite."""

from dataclasses import dataclass

from takt.domain.model.worker_run import WorkerRun


@dataclass(frozen=True, kw_only=True)
class Benchmark:
    """One benchmark with its worker runs."""

    name: str
    """Benchmark name from pyperf metadata."""

    runs: tuple[WorkerRun, ...]
    """Worker runs in file order."""

    def __post_init__(self) -> None:
        """Validate the benchmark invariants.

        :raises ValueError: If an invariant is broken.
        """
        if not self.name:
            msg = 'benchmark name must not be empty'
            raise ValueError(msg)
        if not self.runs:
            msg = 'benchmark must have at least one run'
            raise ValueError(msg)
