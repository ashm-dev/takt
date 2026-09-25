"""Default path of the benchmark result file."""

from datetime import UTC, datetime
from pathlib import Path


def default_output_path(now: datetime, cwd: Path) -> Path:
    """Return the result path used when the user gave no ``-o``.

    :param now: Current time in any timezone.
    :param cwd: Directory where the benchmark runs.
    :returns: ``cwd / takt-<UTC timestamp>.json``.
    """
    stamp = now.astimezone(UTC).strftime('%Y%m%dT%H%M%SZ')
    return cwd / f'takt-{stamp}.json'
