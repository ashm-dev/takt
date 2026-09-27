"""Request to run benchmarks and import the produced result."""

from dataclasses import dataclass

from takt.domain.model.target import Target
from takt.domain.naming.name_template import NameTemplate


@dataclass(frozen=True, kw_only=True)
class RunRequest:
    """Request to run benchmarks and import the produced result."""

    runner_arguments: tuple[str, ...]
    """Arguments of ``takt run`` without takt flags."""

    targets: tuple[Target, ...]
    """Databases to write the imported suite to."""

    name_template: NameTemplate | None
    """Template for the run name, or ``None`` for no name."""
