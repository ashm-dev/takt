"""Result file cannot be read or is not a valid pyperf result."""

from takt.domain.errors.execution_error import ExecutionError


class InvalidResultError(ExecutionError):
    """Result file cannot be read or is not a valid pyperf result."""
