"""Compare operand matches no file and no stored suite."""

from takt.domain.errors.execution_error import ExecutionError


class OperandNotFoundError(ExecutionError):
    """Compare operand matches no file and no stored suite."""
