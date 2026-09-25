"""Process exit codes of the takt command."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Process exit codes of the takt command.

    :cvar OK: Success, including results that were already loaded.
    :cvar FAILURE: Execution error or a write that missed some targets.
    :cvar USAGE: Invalid arguments, configuration or run name.
    :cvar INTERRUPTED: Interrupted with Ctrl+C.
    """

    OK = 0
    FAILURE = 1
    USAGE = 2
    INTERRUPTED = 130
