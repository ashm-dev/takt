"""Database driver for the URL is not installed."""

from takt.domain.errors.configuration_error import ConfigurationError


class MissingDriverError(ConfigurationError):
    """Database driver for the URL is not installed."""
