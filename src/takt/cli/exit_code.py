"""Process exit codes of the takt command."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Process exit codes of the takt command."""

    OK = 0
    """Success, including results that were already loaded."""

    FAILURE = 1
    """Execution error or a write that missed some targets."""

    USAGE = 2
    """Invalid arguments, configuration or run name."""

    INTERRUPTED = 130
    """Interrupted with Ctrl+C."""
