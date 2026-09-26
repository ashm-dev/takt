"""Cause of a Ctrl+C that stopped benchmarks after they wrote a result."""

from pathlib import Path


class BenchmarkInterruptedError(Exception):
    """Cause of a Ctrl+C that stopped benchmarks after they wrote a result.

    It only rides along as ``__cause__`` of the ``KeyboardInterrupt``, so
    Ctrl+C stays a ``KeyboardInterrupt`` for every caller.

    :ivar result_path: New result file with the benchmarks that finished.
    """

    def __init__(self, result_path: Path) -> None:
        """Create the error.

        :param result_path: New result file with the finished benchmarks.
        """
        super().__init__(f'partial result was written to {result_path}')
        self.result_path = result_path
