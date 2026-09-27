"""Database dialect that takt supports."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class DialectInfo:
    """Database dialect that takt supports."""

    backend: str
    """SQLAlchemy backend name, ``"sqlite"`` or ``"mariadb"``."""

    allowed_drivers: tuple[str, ...]
    """Drivers accepted after ``+`` in the URL."""

    driver_module: str | None
    """Module to import for the driver, or ``None``."""

    extra: str | None
    """Package extra that installs the driver, or ``None``."""
