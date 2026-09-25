"""Compared suites have no benchmark in common."""

from takt.domain.errors.execution_error import ExecutionError


class NoCommonBenchmarksError(ExecutionError):
    """Compared suites have no benchmark in common."""
