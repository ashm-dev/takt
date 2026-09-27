"""Building of the compare table from labeled suites."""

import statistics
from collections.abc import Mapping, Sequence
from typing import Final

from takt.domain.compare.compare_table import CompareTable
from takt.domain.compare.labeled_suite import LabeledSuite
from takt.domain.compare.normalized_mean import format_normalized_mean
from takt.domain.compare.significance import is_significant
from takt.domain.compare.value_format import format_value
from takt.domain.errors.no_common_benchmarks_error import (
    NoCommonBenchmarksError,
)
from takt.domain.model.benchmark import Benchmark
from takt.domain.model.suite import Suite

_DEFAULT_UNIT: Final = 'second'
"""Unit assumed when no run of a benchmark names one."""

_NOT_SIGNIFICANT: Final = 'not significant'
"""Cell text for a value that does not differ significantly from the base."""

_BenchmarksByName = Mapping[str, Benchmark]
"""Benchmarks of one suite that have values, keyed by benchmark name."""

_Row = tuple[str, ...]
"""Table row: benchmark name, then one cell per suite."""

_IgnoredOperand = tuple[str, tuple[str, ...]]
"""Operand label and the sorted names of its benchmarks left out."""


def build_compare_table(
    base: LabeledSuite,
    changed: Sequence[LabeledSuite],
) -> CompareTable:
    """Compare changed suites against the base suite.

    :param base: The reference suite.
    :param changed: Suites compared against the base, at least one.
    :returns: The table ``pyperf compare_to --table`` would print.
    :raises ValueError: If ``changed`` is empty.
    :raises NoCommonBenchmarksError: If no benchmark with values is
        present in every suite.
    """
    if not changed:
        msg = 'at least one changed suite is required'
        raise ValueError(msg)
    suites = (base, *changed)
    present = [_benchmarks_with_values(labeled.suite) for labeled in suites]
    common = [
        name
        for name in present[0]
        if all(name in benchmarks for benchmarks in present[1:])
    ]
    if not common:
        msg = 'benchmark suites have no benchmark in common'
        raise NoCommonBenchmarksError(msg)
    return _table(suites, present, common)


def _benchmarks_with_values(suite: Suite) -> _BenchmarksByName:
    return {
        benchmark.name: benchmark
        for benchmark in suite.benchmarks
        if any(run.values for run in benchmark.runs)
    }


def _table(
    suites: Sequence[LabeledSuite],
    present: Sequence[_BenchmarksByName],
    common: Sequence[str],
) -> CompareTable:
    rows: list[_Row] = []
    hidden: list[str] = []
    norm_means: list[list[float]] = [[] for _ in present[1:]]
    for name in common:
        row = _compare_row(name, present, norm_means)
        if row is None:
            hidden.append(name)
        else:
            rows.append(row)
    if len(common) > 1 and rows:
        rows.append(
            (
                'Geometric mean',
                '(ref)',
                *(
                    format_normalized_mean(statistics.geometric_mean(column))
                    for column in norm_means
                ),
            )
        )
    return CompareTable(
        headers=('Benchmark', *(labeled.label for labeled in suites)),
        rows=tuple(rows),
        hidden_not_significant=tuple(hidden),
        ignored=_ignored(suites, common),
    )


def _compare_row(
    name: str,
    present: Sequence[_BenchmarksByName],
    norm_means: Sequence[list[float]],
) -> _Row | None:
    base_values, base_unit = _sample(present[0][name])
    cells = [
        _significant_cell(base_values, benchmarks[name], column_means)
        for benchmarks, column_means in zip(
            present[1:], norm_means, strict=True
        )
    ]
    if all(cell is None for cell in cells):
        return None
    return (
        name,
        format_value(base_unit, statistics.mean(base_values)),
        *(_NOT_SIGNIFICANT if cell is None else cell for cell in cells),
    )


def _significant_cell(
    base_values: Sequence[float],
    benchmark: Benchmark,
    column_means: list[float],
) -> str | None:
    values, unit = _sample(benchmark)
    mean = statistics.mean(values)
    norm_mean = mean / statistics.mean(base_values)
    column_means.append(norm_mean)
    if not is_significant(base_values, values).significant:
        return None
    return ': '.join(
        (
            format_value(unit, mean),
            format_normalized_mean(norm_mean),
        )
    )


def _sample(benchmark: Benchmark) -> tuple[list[float], str]:
    values = [
        measurement.value
        for run in benchmark.runs
        for measurement in run.values
    ]
    units = (run.metadata.unit for run in benchmark.runs)
    unit = next((unit for unit in units if unit is not None), _DEFAULT_UNIT)
    return values, unit


def _ignored(
    suites: Sequence[LabeledSuite],
    common: Sequence[str],
) -> tuple[_IgnoredOperand, ...]:
    ignored: list[_IgnoredOperand] = []
    for labeled in suites:
        names = sorted(
            benchmark.name
            for benchmark in labeled.suite.benchmarks
            if benchmark.name not in common
        )
        if names:
            ignored.append((labeled.label, tuple(names)))
    return tuple(ignored)
