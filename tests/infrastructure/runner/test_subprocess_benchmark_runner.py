import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pyperf
import pytest

from takt.domain.errors.benchmark_failed_error import BenchmarkFailedError
from takt.infrastructure.clock.system_clock import SystemClock
from takt.infrastructure.runner.runner_command import build_runner_command
from takt.infrastructure.runner.subprocess_benchmark_runner import (
    SubprocessBenchmarkRunner,
)

NOW = datetime(2026, 9, 25, 13, 46, 1, tzinfo=UTC)
PY = '/usr/bin/python3.14'
DEFAULT_NAME = 'takt-20260925T134601Z.json'
BENCH_SCRIPT = (
    'import pyperf\n'
    '\n'
    'runner = pyperf.Runner()\n'
    "runner.bench_func('noop', lambda: None)\n"
)

type FakeRun = Callable[..., subprocess.CompletedProcess[bytes]]


class _FixedClock:
    def now(self) -> datetime:
        return NOW


class _Recorder:
    def __init__(
        self,
        *,
        return_code: int,
        creates: Path | None,
        error: OSError | None = None,
    ) -> None:
        self.return_code = return_code
        self.creates = creates
        self.error = error
        self.command: tuple[str, ...] = ()
        self.cwd: Path | None = None

    def __call__(
        self,
        command: tuple[str, ...],
        *,
        check: bool,
        cwd: Path,
    ) -> subprocess.CompletedProcess[bytes]:
        assert not check
        self.command = command
        self.cwd = cwd
        if self.error is not None:
            raise self.error
        if self.creates is not None:
            self.creates.write_text('{}', encoding='utf-8')
        return subprocess.CompletedProcess(command, self.return_code)


def _runner(tmp_path: Path) -> SubprocessBenchmarkRunner:
    return SubprocessBenchmarkRunner(
        clock=_FixedClock(), cwd=tmp_path, python=PY
    )


def _patch(monkeypatch: pytest.MonkeyPatch, fake: FakeRun) -> None:
    monkeypatch.setattr(subprocess, 'run', fake)


def _failure(runner: SubprocessBenchmarkRunner) -> BenchmarkFailedError:
    try:
        runner.run(('-b', 'nbody'))
    except BenchmarkFailedError as error:
        return error
    msg = 'expected BenchmarkFailedError'
    raise AssertionError(msg)


def test_success_returns_default_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = tmp_path / DEFAULT_NAME
    recorder = _Recorder(return_code=0, creates=expected)
    _patch(monkeypatch, recorder)
    assert _runner(tmp_path).run(('-b', 'nbody')) == expected
    command, _ = build_runner_command(
        ('-b', 'nbody'), python=PY, output=expected
    )
    assert recorder.command == command
    assert recorder.cwd == tmp_path


def test_relative_user_output_resolved_against_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, _Recorder(return_code=0, creates=tmp_path / 'r.json'))
    assert _runner(tmp_path).run(('-o', 'r.json')) == tmp_path / 'r.json'


def test_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, _Recorder(return_code=3, creates=None))
    error = _failure(_runner(tmp_path))
    assert error.return_code == 3
    assert str(error).startswith('benchmark command failed with exit code 3: ')
    assert 'pyperformance run' in str(error)


def test_missing_result_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, _Recorder(return_code=0, creates=None))
    error = _failure(_runner(tmp_path))
    assert error.return_code == 0
    missing = tmp_path / DEFAULT_NAME
    assert str(error) == (
        f'benchmark finished but the result file was not created: {missing}'
    )


def test_cannot_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = FileNotFoundError('no python')
    _patch(
        monkeypatch,
        _Recorder(return_code=0, creates=None, error=error),
    )
    failure = _failure(_runner(tmp_path))
    assert failure.return_code == 127
    assert str(failure) == 'cannot start benchmark command: no python'


@pytest.mark.slow
def test_real_pyperf_script(tmp_path: Path) -> None:
    script = tmp_path / 'bench.py'
    script.write_text(BENCH_SCRIPT, encoding='utf-8')
    runner = SubprocessBenchmarkRunner(clock=SystemClock(), cwd=tmp_path)
    path = runner.run((str(script), '--fast', '--processes', '2'))
    assert path.is_file()
    assert path.parent == tmp_path
    suite = pyperf.BenchmarkSuite.load(str(path))
    assert 'noop' in suite.get_benchmark_names()
