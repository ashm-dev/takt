"""Clock that reads the system time."""

from datetime import UTC, datetime


class SystemClock:
    """Clock that reads the system time."""

    def now(self) -> datetime:
        """Return the current time.

        :returns: Timezone-aware time in UTC.
        """
        return datetime.now(UTC)
