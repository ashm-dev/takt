"""Invalid targets, config file or environment variables."""

from takt.domain.errors.usage_error import UsageError


class ConfigurationError(UsageError):
    """Invalid targets, config file or environment variables."""
