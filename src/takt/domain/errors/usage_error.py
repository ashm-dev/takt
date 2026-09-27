"""Error in command line arguments or configuration."""

from typing import ClassVar

from takt.domain.errors.takt_error import TaktError


class UsageError(TaktError):
    """Error in command line arguments or configuration."""

    exit_code: ClassVar[int] = 2
    """Process exit code for bad command line arguments or configuration."""
