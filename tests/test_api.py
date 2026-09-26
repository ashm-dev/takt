import contextlib
import functools
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pyperf
import pytest

import takt
from takt.domain.errors.configuration_error import ConfigurationError
from takt.infrastructure.runner.subprocess_benchmark_runner import (
    SubprocessBenchmarkRunner,
)

NO_TARGETS = (
    'no database targets configured: use --db, --target, TAKT_DB or takt.toml'
)
FAST = (0.1, 0.11, 0.1)
SLOW = (0.2, 0.21, 0.2)
URL = 'sqlite:///a.db'
MISSING = Path('r.json')
SINGLE_STRINGS = (
    (functools.partial(takt.run, 'nbody'), 'runner_arguments'),
    (functools.partial(takt.run, ['-b', 'nbody'], db=URL), 'db'),
    (functools.partial(takt.run, ['-b', 'nbody'], target='local'), 'target'),
    (functools.partial(takt.import_results, MISSING, db=URL), 'db'),
    (functools.partial(takt.import_results, MISSING, target='local'), 'target'),
    (functools.partial(takt.compare, 'ab'), 'operands'),
    (functools.partial(takt.compare, ['a', 'b'], db=URL), 'db'),
    (functools.partial(takt.compare, ['a', 'b'], target='local'), 'target'),
)


class RecordingRun:
    def __init__(self, result_path: Path) -> None:
        self.result_path = result_path
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, arguments: tuple[str, ...]) -> Path:
        self.calls.append(arguments)
        return self.result_path


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    monkeypatch.delenv('TAKT_DB', raising=False)
    monkeypatch.delenv('TAKT_NAME', raising=False)


@pytest.fixture
def result_file(tmp_path: Path) -> Path:
    return write_result(tmp_path / 'result.json', FAST)


def write_result(path: Path, timings: tuple[float, ...]) -> Path:
    worker_run = pyperf.Run(
        list(timings),
        metadata={
            'name': 'nbody',
            'unit': 'second',
            'date': '2026-09-25 10:00:00',
        },
        collect_metadata=False,
    )
    suite = pyperf.BenchmarkSuite([pyperf.Benchmark([worker_run])])
    suite.dump(str(path))
    return path


def sqlite_url(database: Path) -> str:
    return f'sqlite:///{database}'


def suite_rows(database: Path) -> int:
    with contextlib.closing(sqlite3.connect(database)) as connection:
        row = connection.execute('SELECT COUNT(*) FROM takt_suite').fetchone()
    return int(row[0])


def single_outcome(report: takt.ImportReport) -> takt.TargetOutcome:
    assert len(report.write.outcomes) == 1
    return report.write.outcomes[0]


def test_import_to_sqlite(tmp_path: Path, result_file: Path) -> None:
    database = tmp_path / 'a.db'

    report = takt.import_results(
        result_file,
        db=[sqlite_url(database)],
        name='first',
    )

    assert report.write.succeeded is True
    assert report.name == 'first'
    assert single_outcome(report).status == takt.TargetStatus.WRITTEN
    assert suite_rows(database) == 1


def test_import_twice_is_already_loaded(
    tmp_path: Path,
    result_file: Path,
) -> None:
    url = sqlite_url(tmp_path / 'a.db')
    takt.import_results(result_file, db=[url], name='first')

    report = takt.import_results(result_file, db=[url], name='second')

    outcome = single_outcome(report)
    assert outcome.status == takt.TargetStatus.ALREADY_LOADED
    assert outcome.existing_name == 'first'


def test_import_without_targets(result_file: Path) -> None:
    with pytest.raises(ConfigurationError) as error:
        takt.import_results(result_file)

    assert str(error.value) == NO_TARGETS


def test_import_uses_toml(tmp_path: Path, result_file: Path) -> None:
    database = tmp_path / 't.db'
    (tmp_path / 'takt.toml').write_text(
        f'[targets.local]\nurl = "{sqlite_url(database)}"\n',
        encoding='utf-8',
    )

    report = takt.import_results(result_file)

    assert report.write.succeeded is True
    assert suite_rows(database) == 1


def test_run_config_error_does_not_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recording = RecordingRun(tmp_path / 'unused.json')
    monkeypatch.setattr(SubprocessBenchmarkRunner, 'run', recording)

    with pytest.raises(ConfigurationError) as error:
        takt.run(['-b', 'nbody'])

    assert str(error.value) == NO_TARGETS
    assert recording.calls == []


def test_run_imports_runner_result(
    tmp_path: Path,
    result_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recording = RecordingRun(result_file)
    monkeypatch.setattr(SubprocessBenchmarkRunner, 'run', recording)
    url = sqlite_url(tmp_path / 'a.db')

    report = takt.run(['-b', 'nbody'], db=[url])

    assert report.write.succeeded is True
    assert report.result_path == result_file
    assert recording.calls == [('-b', 'nbody')]


@pytest.mark.parametrize(('call', 'parameter'), SINGLE_STRINGS)
def test_single_string_is_rejected(
    call: Callable[..., object],
    parameter: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recording = RecordingRun(tmp_path / 'unused.json')
    monkeypatch.setattr(SubprocessBenchmarkRunner, 'run', recording)

    with pytest.raises(takt.UsageError) as error:
        # A missing config file fails first unless the check runs before it.
        call(config=tmp_path / 'missing.toml')

    assert str(error.value) == (
        f'{parameter} must be a sequence of strings, not a single string'
    )
    assert recording.calls == []


def test_compare_files_without_targets(tmp_path: Path) -> None:
    base = write_result(tmp_path / 'a.json', FAST)
    changed = write_result(tmp_path / 'b.json', SLOW)

    table = takt.compare([str(base), str(changed)])

    assert isinstance(table, takt.CompareTable)
    assert table.headers == ('Benchmark', str(base), str(changed))


def test_compare_db_and_file(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path / 'a.db')
    base = write_result(tmp_path / 'a.json', FAST)
    changed = write_result(tmp_path / 'b.json', SLOW)
    takt.import_results(base, db=[url], name='base')

    table = takt.compare(['base', str(changed)], db=[url])

    assert table.headers == ('Benchmark', 'base', str(changed))


def test_compare_empty_database_raises_execution_error(
    tmp_path: Path,
) -> None:
    url = sqlite_url(tmp_path / 'empty.db')
    changed = write_result(tmp_path / 'b.json', SLOW)

    with pytest.raises(takt.ExecutionError) as caught:
        takt.compare(['base', str(changed)], db=[url])

    engine_url = url.replace('sqlite:', 'sqlite+pysqlite:', 1)
    assert str(caught.value) == (
        f'cannot read from database {engine_url}: no such table: takt_suite'
    )


def test_public_exports() -> None:
    assert set(takt.__all__) == {
        'run',
        'import_results',
        'compare',
        'ImportReport',
        'WriteReport',
        'TargetOutcome',
        'TargetStatus',
        'CompareTable',
        'TaktError',
        'UsageError',
        'ExecutionError',
        '__version__',
    }
    assert isinstance(takt.__version__, str)
