"""Request to compare benchmark suites."""

from dataclasses import dataclass

from takt.domain.model.target import Target


@dataclass(frozen=True, kw_only=True)
class CompareRequest:
    """Request to compare benchmark suites.

    :ivar operands: Operands exactly as the user wrote them, base first.
    :ivar target: Database to look stored runs up in, or ``None``.
    """

    operands: tuple[str, ...]
    target: Target | None
