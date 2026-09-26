"""Benchmark process failed or left no result file."""

from pathlib import Path

from takt.domain.errors.execution_error import ExecutionError


class BenchmarkFailedError(ExecutionError):
    """Benchmark process failed or left no result file.

    :ivar return_code: Exit code of the benchmark process: ``127`` if it
        could not start, ``0`` if it finished without a result file.
    :ivar result_path: Result file that the failed process still wrote,
        or ``None``.
    """

    def __init__(
        self,
        message: str,
        *,
        return_code: int,
        result_path: Path | None = None,
    ) -> None:
        """Create the error.

        :param message: Text shown to the user.
        :param return_code: Exit code of the benchmark process.
        :param result_path: Result file that the failed process still wrote.
        """
        super().__init__(message)
        self.return_code = return_code
        self.result_path = result_path
