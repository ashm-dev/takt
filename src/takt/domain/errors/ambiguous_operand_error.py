"""Compare operand matches several stored suites."""

from takt.domain.errors.execution_error import ExecutionError
from takt.domain.model.suite_summary import SuiteSummary


class AmbiguousOperandError(ExecutionError):
    """Compare operand matches several stored suites."""

    def __init__(
        self,
        message: str,
        *,
        candidates: tuple[SuiteSummary, ...],
    ) -> None:
        """Create the error.

        :param message: Text shown to the user.
        :param candidates: Matching suites in lookup order.
        """
        super().__init__(message)
        self.candidates = candidates
        """Matching suites in lookup order."""
