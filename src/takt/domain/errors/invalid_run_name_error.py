"""Run name template or rendered run name is invalid."""

from takt.domain.errors.usage_error import UsageError


class InvalidRunNameError(UsageError):
    """Run name template or rendered run name is invalid."""
