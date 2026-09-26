"""Date of one pyperf run as naive local time."""

from datetime import datetime


def parse_run_date(date: str | None) -> datetime | None:
    """Parse the ``date`` metadata of a pyperf run.

    pyperf writes naive local time, so a date with a time zone is converted
    to the local time of this machine and loses its time zone; this keeps
    every date comparable.

    :param date: The ``date`` metadata value, or ``None``.
    :returns: A naive datetime, or ``None`` if the date is missing or cannot
        be parsed or converted.
    """
    if date is None:
        return None
    try:
        return _local_naive(datetime.fromisoformat(date))
    # Local time overflows for aware dates at the ends of the datetime range.
    except ValueError, OverflowError:
        return None


def _local_naive(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment
    return moment.astimezone().replace(tzinfo=None)
