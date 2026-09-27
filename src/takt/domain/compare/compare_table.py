"""Result of comparing benchmark suites."""

from dataclasses import dataclass

_IgnoredOperand = tuple[str, tuple[str, ...]]
"""Operand label and the sorted names of its benchmarks left out."""


@dataclass(frozen=True, kw_only=True)
class CompareTable:
    """Table equal to ``pyperf compare_to --table``."""

    headers: tuple[str, ...]
    """``Benchmark``, the base label and the changed labels."""

    rows: tuple[tuple[str, ...], ...]
    """Rows with at least one significant cell, then the ``Geometric mean``
    row when it applies."""

    hidden_not_significant: tuple[str, ...]
    """Benchmarks hidden as not significant."""

    ignored: tuple[_IgnoredOperand, ...]
    """Label and sorted benchmark names for every operand with benchmarks
    outside the common set."""
