"""Outcome of writing a suite to one target."""

from dataclasses import dataclass

from takt.application.multi_target.target_status import TargetStatus
from takt.domain.model.target import Target


@dataclass(frozen=True, kw_only=True)
class TargetOutcome:
    """Outcome of writing a suite to one target."""

    target: Target
    """Target database."""

    status: TargetStatus
    """What happened to the target."""

    existing_name: str | None
    """Name of the stored suite, only for ``already_loaded``."""

    error: str | None
    """Error text, only for ``failed``."""

    def __post_init__(self) -> None:
        """Validate that the optional fields match the status.

        :raises ValueError: If ``existing_name`` or ``error`` is set for a
            wrong status, or ``error`` is missing for ``failed``.
        """
        if (
            self.existing_name is not None
            and self.status is not TargetStatus.ALREADY_LOADED
        ):
            msg = 'existing_name is only allowed for already_loaded'
            raise ValueError(msg)
        if (self.status is TargetStatus.FAILED) != (self.error is not None):
            msg = 'error is required for failed and only allowed for failed'
            raise ValueError(msg)
