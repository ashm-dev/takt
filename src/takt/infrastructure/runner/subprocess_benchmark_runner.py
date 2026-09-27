"""Benchmark runner that starts pyperformance or pyperf in a subprocess."""

import shlex
import subprocess
import sys
from pathlib import Path

from takt.application.ports.clock import Clock
from takt.domain.errors.benchmark_failed_error import BenchmarkFailedError
from takt.domain.errors.benchmark_interrupted_error import (
    BenchmarkInterruptedError,
)
from takt.infrastructure.runner.default_output_path import default_output_path
from takt.infrastructure.runner.output_directory import (
    require_output_directory,
)
from takt.infrastructure.runner.runner_command import build_runner_command

_CANNOT_START_CODE = 127
"""Exit code a shell gives when a command cannot start."""


class SubprocessBenchmarkRunner:
    """Benchmark runner that starts pyperformance or pyperf in a subprocess."""

    def __init__(
        self,
        *,
        clock: Clock,
        cwd: Path,
        python: str = sys.executable,
    ) -> None:
        """Create the runner.

        :param clock: Source of the time for the default result name.
        :param cwd: Directory where the benchmark runs.
        :param python: Interpreter that runs the benchmarks.
        """
        self._clock = clock
        self._cwd = cwd
        self._python = python

    def run(self, arguments: tuple[str, ...]) -> Path:
        """Run benchmarks and return the result file.

        :param arguments: Arguments of ``takt run`` without takt flags.
        :returns: Path to the JSON result.
        :raises BenchmarkFailedError: If the process cannot start, exits
            with a non-zero code or leaves no result file.
        :raises KeyboardInterrupt: On Ctrl+C; its ``__cause__`` is a
            ``BenchmarkInterruptedError`` if the benchmarks had already
            written a new result file.
        :raises UsageError: If ``-o``/``--output`` has no value, or the
            folder of the result file is missing or not writable.
        """
        command, result_path = build_runner_command(
            arguments,
            python=self._python,
            output=default_output_path(self._clock.now(), self._cwd),
            cwd=self._cwd,
        )
        require_output_directory(result_path)
        # The runners never overwrite an output file, so an old one is stale.
        existed = result_path.exists()
        try:
            return_code = self._execute(command)
        except KeyboardInterrupt as interrupt:
            if _is_new_file(result_path, existed=existed):
                # mypyc drops the cause of raise ... from, so it is set here.
                interrupt.__cause__ = BenchmarkInterruptedError(result_path)
            raise
        if return_code != 0:
            written = _is_new_file(result_path, existed=existed)
            raise _failed(
                command,
                return_code,
                result_path if written else None,
            )
        return self._require_file(result_path)

    def _execute(self, command: tuple[str, ...]) -> int:
        try:
            completed = subprocess.run(  # noqa: S603 - arguments are passed as a tuple without a shell
                command,
                check=False,
                cwd=self._cwd,
            )
        except OSError as exc:
            message = f'cannot start benchmark command: {exc}'
            raise BenchmarkFailedError(
                message,
                return_code=_CANNOT_START_CODE,
            ) from exc
        return completed.returncode

    def _require_file(self, result_path: Path) -> Path:
        if not result_path.is_file():
            message = (
                'benchmark finished but the result file was not created: '
                f'{result_path}'
            )
            raise BenchmarkFailedError(message, return_code=0)
        return result_path


def _is_new_file(result_path: Path, *, existed: bool) -> bool:
    return not existed and result_path.is_file()


def _failed(
    command: tuple[str, ...],
    return_code: int,
    result_path: Path | None,
) -> BenchmarkFailedError:
    message = (
        'benchmark command failed with exit code '
        f'{return_code}: {shlex.join(command)}'
    )
    return BenchmarkFailedError(
        message,
        return_code=return_code,
        result_path=result_path,
    )
