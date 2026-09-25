"""Database URL uses a dialect that takt does not support."""

from takt.domain.errors.configuration_error import ConfigurationError


class UnsupportedDialectError(ConfigurationError):
    """Database URL uses a dialect that takt does not support."""
