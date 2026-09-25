"""Report of importing a pyperf result into database targets."""

from dataclasses import dataclass
from pathlib import Path

from takt.application.multi_target.write_report import WriteReport


@dataclass(frozen=True, kw_only=True)
class ImportReport:
    """Report of importing a pyperf result into database targets.

    :ivar result_path: Path to the pyperf result file that was imported.
    :ivar suite_hash: Hash of the imported suite.
    :ivar name: Run name computed for this import, even when not stored.
    :ivar write: Per-target outcomes of the write.
    """

    result_path: Path
    suite_hash: str
    name: str | None
    write: WriteReport
