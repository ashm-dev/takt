"""Source of the current time."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Source of the current time."""

    def now(self) -> datetime:
        """Return the current time.

        :returns: Timezone-aware time in UTC.
        """
