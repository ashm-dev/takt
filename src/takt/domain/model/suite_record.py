"""Suite together with its storage attributes."""

from dataclasses import dataclass
from datetime import datetime

from takt.domain.model.suite import Suite
from takt.domain.model.suite_source import SuiteSource


@dataclass(frozen=True, kw_only=True)
class SuiteRecord:
    """Suite with the attributes that exist only in storage.

    :ivar suite: The suite itself.
    :ivar name: Run name or ``None``.
    :ivar source: Command that stored the suite.
    :ivar loaded_at: Storage time in UTC.
    """

    suite: Suite
    name: str | None
    source: SuiteSource
    loaded_at: datetime
