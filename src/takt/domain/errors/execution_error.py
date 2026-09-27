"""Error while running a command."""

from typing import ClassVar

from takt.domain.errors.takt_error import TaktError


class ExecutionError(TaktError):
    """Error while running a command."""

    exit_code: ClassVar[int] = 1
    """Process exit code when a command fails while it runs."""
