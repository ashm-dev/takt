"""Result of writing a suite to one target."""

from enum import StrEnum


class TargetStatus(StrEnum):
    """What happened to one target during an all-or-nothing write."""

    WRITTEN = 'written'
    """The suite was inserted and committed."""

    ALREADY_LOADED = 'already_loaded'
    """The target already had the suite, so nothing was written."""

    FAILED = 'failed'
    """Writing to this target raised an error."""

    ROLLED_BACK = 'rolled_back'
    """The write was undone because another target failed."""

    NOT_ATTEMPTED = 'not_attempted'
    """The write stopped before it reached this target."""
