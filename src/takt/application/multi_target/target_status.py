"""Result of writing a suite to one target."""

from enum import StrEnum


class TargetStatus(StrEnum):
    """What happened to one target during an all-or-nothing write."""

    WRITTEN = 'written'
    ALREADY_LOADED = 'already_loaded'
    FAILED = 'failed'
    ROLLED_BACK = 'rolled_back'
    NOT_ATTEMPTED = 'not_attempted'
