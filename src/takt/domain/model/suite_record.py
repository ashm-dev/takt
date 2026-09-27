"""Suite together with its storage attributes."""

from dataclasses import dataclass
from datetime import datetime

from takt.domain.model.suite import Suite
from takt.domain.model.suite_source import SuiteSource


@dataclass(frozen=True, kw_only=True)
class SuiteRecord:
    """Suite with the attributes that exist only in storage."""

    suite: Suite
    """The suite itself."""

    name: str | None
    """Run name or ``None``."""

    source: SuiteSource
    """Command that stored the suite."""

    loaded_at: datetime
    """Storage time in UTC."""
