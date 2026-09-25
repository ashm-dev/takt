"""Database dialect that takt supports."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class DialectInfo:
    """Database dialect that takt supports.

    :ivar backend: SQLAlchemy backend name, ``"sqlite"`` or ``"mariadb"``.
    :ivar allowed_drivers: Drivers accepted after ``+`` in the URL.
    :ivar driver_module: Module to import for the driver, or ``None``.
    """

    backend: str
    allowed_drivers: tuple[str, ...]
    driver_module: str | None
