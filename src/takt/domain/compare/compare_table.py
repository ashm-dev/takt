"""Result of comparing benchmark suites."""

from dataclasses import dataclass

_IgnoredOperand = tuple[str, tuple[str, ...]]


@dataclass(frozen=True, kw_only=True)
class CompareTable:
    """Table equal to ``pyperf compare_to --table``.

    :ivar headers: ``Benchmark``, the base label and the changed labels.
    :ivar rows: Rows with at least one significant cell, then the
        ``Geometric mean`` row when it applies.
    :ivar hidden_not_significant: Benchmarks hidden as not significant.
    :ivar ignored: Label and sorted benchmark names for every operand
        with benchmarks outside the common set.
    """

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    hidden_not_significant: tuple[str, ...]
    ignored: tuple[_IgnoredOperand, ...]
