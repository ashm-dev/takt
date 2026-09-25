import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pyperf

from takt.domain.compare.build_compare_table import build_compare_table
from takt.domain.compare.labeled_suite import LabeledSuite
from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.run_metadata import RunMetadata
from takt.domain.model.suite import Suite
from takt.domain.model.worker_run import WorkerRun

Runs = Sequence[Sequence[float]]
Named = Sequence[tuple[str, Runs]]

BASE: Named = (
    ('fast', ((0.01, 0.011, 0.01), (0.01, 0.012, 0.011))),
    ('slow', ((0.5, 0.52, 0.51), (0.5, 0.51, 0.52))),
    ('same', ((0.2, 0.21, 0.2), (0.21, 0.2, 0.21))),
)
CHANGED: Named = (
    ('fast', ((0.008, 0.009, 0.008), (0.008, 0.009, 0.009))),
    ('slow', ((0.6, 0.61, 0.62), (0.6, 0.62, 0.61))),
    ('same', ((0.21, 0.2, 0.21), (0.2, 0.21, 0.2))),
)
HIDDEN_PREFIX = 'Benchmark hidden because not significant'


def _dump_pyperf(benchmarks: Named, path: Path) -> str:
    suite = pyperf.BenchmarkSuite(
        [
            pyperf.Benchmark(
                [
                    pyperf.Run(
                        list(values),
                        metadata={'name': name, 'unit': 'second'},
                        collect_metadata=False,
                    )
                    for values in runs
                ]
            )
            for name, runs in benchmarks
        ]
    )
    suite.dump(str(path))
    return str(path)


def _measurements(values: Sequence[float]) -> tuple[Measurement, ...]:
    return tuple(
        Measurement(kind=MeasurementKind.VALUE, value=value, loops=None)
        for value in values
    )


def _takt_suite(label: str, benchmarks: Named) -> LabeledSuite:
    built = tuple(
        Benchmark(
            name=name,
            runs=tuple(
                WorkerRun(
                    metadata=RunMetadata(name=name, unit='second'),
                    warmups=(),
                    values=_measurements(values),
                )
                for values in runs
            ),
        )
        for name, runs in benchmarks
    )
    suite = Suite(
        hash='a' * 64,
        format_version='1.0',
        result_date=None,
        benchmarks=built,
    )
    return LabeledSuite(label=label, suite=suite)


def _pyperf_stdout(tmp_path: Path) -> list[str]:
    completed = subprocess.run(  # noqa: S603 - arguments are passed as a list without a shell
        [
            sys.executable,
            '-m',
            'pyperf',
            'compare_to',
            '--table',
            '--table-format=md',
            _dump_pyperf(BASE, tmp_path / 'base.json'),
            _dump_pyperf(CHANGED, tmp_path / 'changed.json'),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.splitlines()


def _cells(line: str) -> list[str]:
    inner = line.split('|')[1:-1]
    return [cell.strip() for cell in inner]


def _table_rows(lines: Sequence[str]) -> list[list[str]]:
    table_lines = [line for line in lines if line.startswith('|')][2:]
    return [_cells(line) for line in table_lines]


def test_matches_pyperf_compare_to(tmp_path: Path) -> None:
    lines = _pyperf_stdout(tmp_path)

    table = build_compare_table(
        _takt_suite('base.json', BASE),
        [_takt_suite('changed.json', CHANGED)],
    )

    assert [list(row) for row in table.rows] == _table_rows(lines)
    hidden = [line for line in lines if line.startswith(HIDDEN_PREFIX)]
    for line in hidden:
        names = tuple(line.partition(': ')[2].split(', '))
        assert names == table.hidden_not_significant
