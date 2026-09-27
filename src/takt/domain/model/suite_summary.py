"""Short description of a stored suite."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class SuiteSummary:
    """Short description of a stored suite for lookups."""

    hash: str
    """Suite hash."""

    name: str | None
    """Run name or ``None``."""

    result_date: datetime | None
    """Earliest run date or ``None``."""
