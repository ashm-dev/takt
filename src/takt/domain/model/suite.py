"""Benchmark suite: one pyperf result file."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from takt.domain.model.benchmark import Benchmark

_HASH_PATTERN: Final = re.compile('[0-9a-f]{64}')
"""Valid suite hash: 64 lowercase hex characters."""


@dataclass(frozen=True, kw_only=True)
class Suite:
    """One pyperf result file."""

    hash: str
    """SHA-256 of the canonical JSON in lowercase hex."""

    format_version: str
    """pyperf JSON format version."""

    result_date: datetime | None
    """Earliest run date, naive local time."""

    benchmarks: tuple[Benchmark, ...]
    """Benchmarks in file order."""

    def __post_init__(self) -> None:
        """Validate the suite invariants.

        :raises ValueError: If an invariant is broken.
        """
        if _HASH_PATTERN.fullmatch(self.hash) is None:
            msg = 'suite hash must be 64 lowercase hex characters'
            raise ValueError(msg)
        if not self.benchmarks:
            msg = 'suite must have at least one benchmark'
            raise ValueError(msg)
        names = {benchmark.name for benchmark in self.benchmarks}
        if len(names) != len(self.benchmarks):
            msg = 'benchmark names must be unique'
            raise ValueError(msg)
