"""Report of importing a pyperf result into database targets."""

from dataclasses import dataclass
from pathlib import Path

from takt.application.multi_target.write_report import WriteReport


@dataclass(frozen=True, kw_only=True)
class ImportReport:
    """Report of importing a pyperf result into database targets."""

    result_path: Path
    """Path to the pyperf result file that was imported."""

    suite_hash: str
    """Hash of the imported suite."""

    name: str | None
    """Run name computed for this import, even when not stored."""

    write: WriteReport
    """Per-target outcomes of the write."""
