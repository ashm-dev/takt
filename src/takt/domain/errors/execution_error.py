"""Error while running a command."""

from typing import ClassVar

from takt.domain.errors.takt_error import TaktError


class ExecutionError(TaktError):
    """Error while running a command.

    :cvar exit_code: Always ``1``.
    """

    exit_code: ClassVar[int] = 1
