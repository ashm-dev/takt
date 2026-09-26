"""Request to compare benchmark suites."""

import os
from collections.abc import Callable
from dataclasses import dataclass

from takt.domain.model.target import Target


@dataclass(frozen=True, kw_only=True)
class CompareRequest:
    """Request to compare benchmark suites.

    :ivar operands: Operands exactly as the user wrote them, base first;
        a path object always names a result file.
    :ivar find_target: Returns the database to look stored runs up in, or
        ``None``; it is called only when an operand is not a file, so a
        broken database setting never stops a compare of files.
    """

    operands: tuple[str | os.PathLike[str], ...]
    find_target: Callable[[], Target | None]
