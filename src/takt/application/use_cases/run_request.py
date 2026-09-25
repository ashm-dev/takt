"""Request to run benchmarks and import the produced result."""

from dataclasses import dataclass

from takt.domain.model.target import Target
from takt.domain.naming.name_template import NameTemplate


@dataclass(frozen=True, kw_only=True)
class RunRequest:
    """Request to run benchmarks and import the produced result.

    :ivar runner_arguments: Arguments of ``takt run`` without takt flags.
    :ivar targets: Databases to write the imported suite to.
    :ivar name_template: Template for the run name, or ``None`` for no name.
    """

    runner_arguments: tuple[str, ...]
    targets: tuple[Target, ...]
    name_template: NameTemplate | None
