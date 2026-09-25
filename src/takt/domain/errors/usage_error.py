"""Error in command line arguments or configuration."""

from typing import ClassVar

from takt.domain.errors.takt_error import TaktError


class UsageError(TaktError):
    """Error in command line arguments or configuration.

    :cvar exit_code: Always ``2``.
    """

    exit_code: ClassVar[int] = 2
