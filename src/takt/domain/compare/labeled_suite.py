"""Suite taking part in a comparison together with its label."""

from dataclasses import dataclass

from takt.domain.model.suite import Suite


@dataclass(frozen=True, kw_only=True)
class LabeledSuite:
    """Suite taking part in a comparison.

    :ivar label: Operand exactly as the user wrote it.
    :ivar suite: The suite behind the operand.
    """

    label: str
    suite: Suite
