"""Outcomes of writing a suite to every target."""

from dataclasses import dataclass

from takt.application.multi_target.target_outcome import TargetOutcome
from takt.application.multi_target.target_status import TargetStatus


@dataclass(frozen=True, kw_only=True)
class WriteReport:
    """Outcomes of writing a suite to every target."""

    outcomes: tuple[TargetOutcome, ...]
    """One outcome per target, in the order of the targets."""

    @property
    def succeeded(self) -> bool:
        """Tell whether the suite is stored in every target.

        :returns: ``True`` when every status is written or already loaded.
        """
        return all(
            outcome.status
            in {TargetStatus.WRITTEN, TargetStatus.ALREADY_LOADED}
            for outcome in self.outcomes
        )
