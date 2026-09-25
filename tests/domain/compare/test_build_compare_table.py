import statistics
from collections.abc import Mapping, Sequence

import pytest

from takt.domain.compare.build_compare_table import build_compare_table
from takt.domain.compare.compare_table import CompareTable
from takt.domain.compare.labeled_suite import LabeledSuite
from takt.domain.compare.normalized_mean import format_normalized_mean
from takt.domain.errors.no_common_benchmarks_error import (
    NoCommonBenchmarksError,
)
from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.suite import Suite
from takt.domain.model.worker_run import WorkerRun

Runs = Sequence[Sequence[float]]

HASH = 'a' * 64
ONE = ((1.0,),)
TWO = ((2.0,),)
HALF = ((0.5,),)
SPREAD = ((1.0, 2.0),)
SPREAD_REVERSED = ((2.0, 1.0),)


def _run(name: str, values: Sequence[float], unit: str | None) -> WorkerRun:
    return WorkerRun(
        metadata=RunMetadata(name=name, unit=unit),
        warmups=(),
        values=tuple(
            Measurement(kind=MeasurementKind.VALUE, value=value, loops=None)
            for value in values
        ),
    )


def _calibration_run(name: str) -> WorkerRun:
    warmup = Measurement(kind=MeasurementKind.WARMUP, value=0.1, loops=1)
    return WorkerRun(
        metadata=RunMetadata(name=name),
        warmups=(warmup,),
        values=(),
    )


def _suite(
    label: str,
    benchmarks: Mapping[str, Runs],
    unit: str | None = 'second',
    extra: tuple[Benchmark, ...] = (),
) -> LabeledSuite:
    built = tuple(
        Benchmark(
            name=name,
            runs=tuple(_run(name, values, unit) for values in runs),
        )
        for name, runs in benchmarks.items()
    )
    suite = Suite(
        hash=HASH,
        format_version='1.0',
        result_date=None,
        benchmarks=built + extra,
    )
    return LabeledSuite(label=label, suite=suite)


def _compare(
    base: Mapping[str, Runs],
    changed: Mapping[str, Runs],
    unit: str | None = 'second',
) -> CompareTable:
    return build_compare_table(
        _suite('base', base, unit),
        [_suite('changed', changed, unit)],
    )


def test_basic_table() -> None:
    base = _suite('base.json', {'nbody': [[0.1, 0.1, 0.1, 0.1]]})
    changed = _suite('new.json', {'nbody': [[0.09, 0.09, 0.09, 0.09]]})

    table = build_compare_table(base, [changed])

    assert table.headers == ('Benchmark', 'base.json', 'new.json')
    assert table.rows == (('nbody', '100 ms', '90.0 ms: 1.11x faster'),)
    assert table.hidden_not_significant == ()
    assert table.ignored == ()


def test_not_significant_row_is_hidden() -> None:
    table = _compare(
        {
            'a': [[1.0, 2.0, 1.0, 2.0]],
            'b': [[1.0, 1.1, 0.9, 1.0]],
        },
        {
            'a': [[2.0, 1.0, 2.0, 1.0]],
            'b': [[2.0, 2.1, 1.9, 2.0]],
        },
    )

    assert [row[0] for row in table.rows] == ['b', 'Geometric mean']
    assert table.hidden_not_significant == ('a',)
    expected = format_normalized_mean(statistics.geometric_mean([1.0, 2.0]))
    assert expected == '1.41x slower'
    assert table.rows[-1] == ('Geometric mean', '(ref)', expected)


def test_geometric_mean_needs_two_common() -> None:
    table = _compare({'a': ONE, 'only_base': ONE}, {'a': TWO})

    assert table.rows == (('a', '1.00 sec', '2.00 sec: 2.00x slower'),)


def test_no_rows_no_geometric_mean() -> None:
    table = _compare(
        {'b': SPREAD, 'a': SPREAD},
        {'a': SPREAD_REVERSED, 'b': SPREAD_REVERSED},
    )

    assert table.rows == ()
    assert table.hidden_not_significant == ('b', 'a')


def test_common_is_intersection_in_base_order() -> None:
    base = _suite('base', {'c': ONE, 'a': ONE, 'b': ONE})
    changed1 = _suite('changed1', {'a': TWO, 'b': TWO, 'c': TWO})
    changed2 = _suite('changed2', {'b': HALF, 'c': HALF})

    table = build_compare_table(base, [changed1, changed2])

    assert [row[0] for row in table.rows] == ['c', 'b', 'Geometric mean']
    assert table.ignored == (('base', ('a',)), ('changed1', ('a',)))


def test_no_common() -> None:
    with pytest.raises(
        NoCommonBenchmarksError,
        match='benchmark suites have no benchmark in common',
    ):
        _compare({'a': ONE}, {'b': ONE})


def test_benchmark_without_values_is_absent() -> None:
    base = _suite('base', {'a': ONE, 'x': ONE})
    calibration = Benchmark(name='x', runs=(_calibration_run('x'),))
    changed = _suite('changed', {'a': TWO}, extra=(calibration,))

    table = build_compare_table(base, [changed])

    assert [row[0] for row in table.rows] == ['a']
    assert table.ignored == (('base', ('x',)), ('changed', ('x',)))


def test_three_operands() -> None:
    base = _suite('base', {'a': ONE, 'b': ONE})
    changed1 = _suite('changed1', {'a': TWO, 'b': TWO})
    changed2 = _suite('changed2', {'a': HALF, 'b': HALF})

    table = build_compare_table(base, [changed1, changed2])

    assert table.headers == ('Benchmark', 'base', 'changed1', 'changed2')
    assert table.rows[0] == (
        'a',
        '1.00 sec',
        '2.00 sec: 2.00x slower',
        '500 ms: 2.00x faster',
    )
    assert table.rows[-1] == (
        'Geometric mean',
        '(ref)',
        '2.00x slower',
        '2.00x faster',
    )


def test_unit_from_metadata() -> None:
    base = {'mem': ((1000.0,),)}
    changed = {'mem': ((2000.0,),)}

    table = _compare(base, changed, unit='byte')

    assert table.rows == (('mem', '1000 bytes', '2000 bytes: 2.00x slower'),)


def test_missing_unit_defaults_to_second() -> None:
    table = _compare({'a': ONE}, {'a': TWO}, unit=None)

    assert table.rows == (('a', '1.00 sec', '2.00 sec: 2.00x slower'),)


def test_empty_changed() -> None:
    base = _suite('base', {'a': ONE})

    with pytest.raises(ValueError, match='at least one changed suite'):
        build_compare_table(base, [])
