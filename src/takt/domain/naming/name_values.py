"""Values used to render a run name template."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class NameValues:
    """Values available for a :class:`NameTemplate` to render.

    :ivar now: Import time, UTC.
    :ivar result_path: Path to the pyperf result file.
    :ivar python_version: Interpreter version reported by pyperf, if known.
    :ivar hostname: Host that produced the result, if known.
    :ivar suite_hash: Full hash of the suite.
    """

    now: datetime
    result_path: Path
    python_version: str | None
    hostname: str | None
    suite_hash: str
