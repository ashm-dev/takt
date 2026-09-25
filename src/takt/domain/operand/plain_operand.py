"""Compare operand without a ':' and without a matching file."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class PlainOperand:
    """Compare operand tried first as a run name, then as a hash prefix.

    :ivar text: Operand text as the user wrote it.
    """

    text: str
