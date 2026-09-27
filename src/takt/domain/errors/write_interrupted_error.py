"""Cause of a Ctrl+C that stopped the database write of a result."""

from pathlib import Path


class WriteInterruptedError(Exception):
    """Cause of a Ctrl+C that stopped the database write of a result.

    It only rides along as ``__cause__`` of the ``KeyboardInterrupt``, so
    Ctrl+C stays a ``KeyboardInterrupt`` for every caller.
    """

    def __init__(self, result_path: Path, name: str | None) -> None:
        """Create the error.

        :param result_path: Complete result file that was being written.
        :param name: Run name given to the result, or ``None``.
        """
        super().__init__(f'writing of {result_path} was interrupted')
        self.result_path = result_path
        """Complete result file that was being written."""

        self.name = name
        """Run name given to the result, or ``None``."""
