"""Run name template or rendered run name is invalid."""

from pathlib import Path

from takt.domain.errors.usage_error import UsageError


class InvalidRunNameError(UsageError):
    """Run name template or rendered run name is invalid."""

    def __init__(
        self,
        message: str,
        *,
        result_path: Path | None = None,
    ) -> None:
        """Create the error.

        :param message: Text shown to the user.
        :param result_path: Result file that the benchmarks already wrote.
        """
        super().__init__(message)
        self.result_path = result_path
        """Result file that ``takt run`` produced before the final name was
        checked, or ``None``."""
