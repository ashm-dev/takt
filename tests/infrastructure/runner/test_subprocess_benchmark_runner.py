import subprocess
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
from tests.domain.exact_pattern import exact_pattern

NOW = datetime(2026, 9, 25, 13, 46, 1, tzinfo=UTC)
PY = '/usr/bin/python3.14'
DEFAULT_NAME = 'takt-20260925T134601Z.json'
BENCH_SCRIPT = (
    'import pyperf\n'
    '\n'
    'runner = pyperf.Runner()\n'
    "runner.bench_func('noop', lambda: None)\n"
)


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


def _patch(monkeypatch: pytest.MonkeyPatch, fake: _Recorder) -> None:
    monkeypatch.setattr(subprocess, 'run', fake)


def _exit_message(tmp_path: Path, return_code: int) -> str:
    output = tmp_path / DEFAULT_NAME
    return (
        f'benchmark command failed with exit code {return_code}: '
        f'{PY} -m pyperformance run -b nbody --output {output}'
    )


def test_success_returns_default_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = tmp_path / DEFAULT_NAME
    recorder = _Recorder(return_code=0, creates=expected)
    _patch(monkeypatch, recorder)
    assert _runner(tmp_path).run(('-b', 'nbody')) == expected
    command, _ = build_runner_command(
        ('-b', 'nbody'), python=PY, output=expected, cwd=tmp_path
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
    message = _exit_message(tmp_path, 3)
    with pytest.raises(
        BenchmarkFailedError, match=exact_pattern(message)
    ) as error:
        _runner(tmp_path).run(('-b', 'nbody'))
    assert error.value.return_code == 3
    assert error.value.result_path is None


def test_nonzero_exit_keeps_partial_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    partial = tmp_path / DEFAULT_NAME
    _patch(monkeypatch, _Recorder(return_code=1, creates=partial))
    message = _exit_message(tmp_path, 1)
    with pytest.raises(
        BenchmarkFailedError, match=exact_pattern(message)
    ) as error:
        _runner(tmp_path).run(('-b', 'nbody'))
    assert error.value.return_code == 1
    assert error.value.result_path == partial


def test_nonzero_exit_ignores_old_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / DEFAULT_NAME).write_text('{}', encoding='utf-8')
    _patch(monkeypatch, _Recorder(return_code=1, creates=None))
    message = _exit_message(tmp_path, 1)
    with pytest.raises(
        BenchmarkFailedError, match=exact_pattern(message)
    ) as error:
        _runner(tmp_path).run(('-b', 'nbody'))
    assert error.value.result_path is None


def test_missing_result_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch(monkeypatch, _Recorder(return_code=0, creates=None))
    missing = tmp_path / DEFAULT_NAME
    message = (
        f'benchmark finished but the result file was not created: {missing}'
    )
    with pytest.raises(
        BenchmarkFailedError, match=exact_pattern(message)
    ) as error:
        _runner(tmp_path).run(('-b', 'nbody'))
    assert error.value.return_code == 0


def test_cannot_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cause = FileNotFoundError('no python')
    _patch(
        monkeypatch,
        _Recorder(return_code=0, creates=None, error=cause),
    )
    message = 'cannot start benchmark command: no python'
    with pytest.raises(
        BenchmarkFailedError, match=exact_pattern(message)
    ) as error:
        _runner(tmp_path).run(('-b', 'nbody'))
    assert error.value.return_code == 127


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
