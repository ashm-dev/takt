"""Base error of takt."""

from typing import ClassVar


class TaktError(Exception):
    """Base class for errors that takt reports without a traceback.

    :cvar exit_code: Process exit code for this error.
    """

    exit_code: ClassVar[int] = 1
