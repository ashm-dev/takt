"""Benchmark process exited with a non-zero code."""

from takt.domain.errors.execution_error import ExecutionError


class BenchmarkFailedError(ExecutionError):
    """Benchmark process exited with a non-zero code.

    :ivar return_code: Exit code of the benchmark process.
    """

    def __init__(self, message: str, *, return_code: int) -> None:
        """Create the error.

        :param message: Text shown to the user.
        :param return_code: Exit code of the benchmark process.
        """
        super().__init__(message)
        self.return_code = return_code
