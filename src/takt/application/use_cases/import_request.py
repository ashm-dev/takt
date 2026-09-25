"""Request to import a pyperf result into database targets."""

from dataclasses import dataclass
from pathlib import Path

from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.target import Target
from takt.domain.naming.name_template import NameTemplate


@dataclass(frozen=True, kw_only=True)
class ImportRequest:
    """Request to import a pyperf result into database targets.

    :ivar path: Path to the pyperf JSON or JSON.gz result file.
    :ivar targets: Databases to write the suite to.
    :ivar name_template: Template for the run name, or ``None`` for no name.
    :ivar source: Command that triggered the import.
    """

    path: Path
    targets: tuple[Target, ...]
    name_template: NameTemplate | None
    source: SuiteSource
