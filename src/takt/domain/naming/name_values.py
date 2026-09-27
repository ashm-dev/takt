"""Values used to render a run name template."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class NameValues:
    """Values available for a :class:`NameTemplate` to render."""

    now: datetime
    """Import time, UTC."""

    result_path: Path
    """Path to the pyperf result file."""

    python_version: str | None
    """Interpreter version reported by pyperf, if known."""

    hostname: str | None
    """Host that produced the result, if known."""

    suite_hash: str
    """Full hash of the suite."""
