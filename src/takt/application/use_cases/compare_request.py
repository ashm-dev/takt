"""Request to compare benchmark suites."""

import os
from dataclasses import dataclass

from takt.domain.model.target import Target


@dataclass(frozen=True, kw_only=True)
class CompareRequest:
    """Request to compare benchmark suites.

    :ivar operands: Operands exactly as the user wrote them, base first;
        a path object always names a result file.
    :ivar target: Database to look stored runs up in, or ``None``.
    """

    operands: tuple[str | os.PathLike[str], ...]
    target: Target | None
