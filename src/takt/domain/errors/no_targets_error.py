"""No database target is configured."""

from takt.domain.errors.configuration_error import ConfigurationError

_MESSAGE = (
    'no database targets configured: use --db, --target, TAKT_DB or takt.toml'
)
"""Error text that lists every way to configure a database target."""


class NoTargetsError(ConfigurationError):
    """No database target is configured."""

    def __init__(self) -> None:
        """Create the error with its fixed message."""
        super().__init__(_MESSAGE)
