"""Request to import a pyperf result into database targets."""

from dataclasses import dataclass
from pathlib import Path

from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.target import Target
from takt.domain.naming.name_template import NameTemplate


@dataclass(frozen=True, kw_only=True)
class ImportRequest:
    """Request to import a pyperf result into database targets."""

    path: Path
    """Path to the pyperf JSON or JSON.gz result file."""

    targets: tuple[Target, ...]
    """Databases to write the suite to."""

    name_template: NameTemplate | None
    """Template for the run name, or ``None`` for no name."""

    source: SuiteSource
    """Command that triggered the import."""
