"""Short description of a stored suite."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class SuiteSummary:
    """Short description of a stored suite for lookups.

    :ivar hash: Suite hash.
    :ivar name: Run name or ``None``.
    :ivar result_date: Earliest run date or ``None``.
    """

    hash: str
    name: str | None
    result_date: datetime | None
