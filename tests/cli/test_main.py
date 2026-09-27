import dataclasses
import functools
import io
import re
import sys
from collections.abc import Callable
from pathlib import Path
from types import MappingProxyType

import pytest

from takt import api
from takt.cli.main import main
from takt.domain.compare.compare_table import CompareTable
from takt.domain.errors.benchmark_failed_error import BenchmarkFailedError
from takt.domain.errors.benchmark_interrupted_error import (
    BenchmarkInterruptedError,
)
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.errors.write_interrupted_error import WriteInterruptedError
from tests.cli.reports import FAILED_REPORT, OK_REPORT

NO_TARGETS = (
    'no database targets configured: use --db, --target, TAKT_DB or takt.toml'
)
"""Error text when no database target is configured."""

SNAPSHOT_TABLE = CompareTable(
    headers=('Benchmark', 'base.json', 'new.json'),
    rows=(('nbody', '100 ms', '90.0 ms: 1.11x faster'),),
    hidden_not_significant=(),
    ignored=(),
)
"""Compare table the fake ``compare`` returns."""

TARGET_ARGV = (
    '--db',
    'sqlite:///a.db',
    '--target',
    'ci',
    '--config',
    'ci.toml',
)
"""Target options added to a command line."""

TARGET_KWARGS = MappingProxyType(
    {
        'db': ['sqlite:///a.db'],
        'target': ['ci'],
        'config': Path('ci.toml'),
    },
)
"""Keyword arguments the CLI passes to the API for ``TARGET_ARGV``."""

SNAPSHOT_MARKDOWN = (
    '| Benchmark | base.json | new.json              |\n'
    '|-----------|:---------:|:---------------------:|\n'
    '| nbody     | 100 ms    | 90.0 ms: 1.11x faster |\n'
)
"""Markdown that ``SNAPSHOT_TABLE`` must render to."""


class Recorder:
    def __init__(self, response: object) -> None:
        self.response = response
        self.args: tuple[object, ...] = ()
        self.kwargs: dict[str, object] = {}

    def __call__(self, *args: object, **kwargs: object) -> object:
        self.args = args
        self.kwargs = kwargs
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


class BufferedOutput(io.StringIO):
    def __init__(self, log: list[str]) -> None:
        super().__init__()
        self.log = log

    def flush(self) -> None:
        self.log.append(self.getvalue())
        self.seek(0)
        self.truncate()


class DirectOutput(io.StringIO):
    def __init__(self, log: list[str]) -> None:
        super().__init__()
        self.log = log

    def write(self, text: str) -> int:
        self.log.append(text)
        return len(text)


def plain_output(capsys: pytest.CaptureFixture[str]) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', capsys.readouterr().out)


@pytest.fixture
def fake_api(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[str, object], Recorder]:
    return functools.partial(_install, monkeypatch)


def _install(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
    response: object,
) -> Recorder:
    recorder = Recorder(response)
    monkeypatch.setattr(api, function_name, recorder)
    return recorder


def test_import_ok(fake_api: Callable[[str, object], Recorder]) -> None:
    fake = fake_api('import_results', OK_REPORT)

    code = main(['import', 'r.json', '--db', 'sqlite:///a.db'])

    assert code == 0
    assert fake.args == (Path('r.json'),)
    assert fake.kwargs['db'] == ['sqlite:///a.db']


@pytest.mark.parametrize(
    ('argv', 'function_name', 'response', 'expected'),
    [
        (
            ['run', '-b', 'nbody', *TARGET_ARGV, '--name', 'x'],
            'run',
            OK_REPORT,
            {**TARGET_KWARGS, 'name': 'x'},
        ),
        (
            ['import', 'r.json', *TARGET_ARGV, '--name', 'x'],
            'import_results',
            OK_REPORT,
            {**TARGET_KWARGS, 'name': 'x'},
        ),
        (
            ['compare', 'a', 'b', *TARGET_ARGV],
            'compare',
            SNAPSHOT_TABLE,
            dict(TARGET_KWARGS),
        ),
    ],
)
def test_flags_reach_api(
    fake_api: Callable[[str, object], Recorder],
    argv: list[str],
    function_name: str,
    response: object,
    expected: dict[str, object],
) -> None:
    fake = fake_api(function_name, response)

    assert main(argv) == 0
    assert fake.kwargs == expected


def test_import_failed_write(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api('import_results', FAILED_REPORT)

    code = main(['import', 'r.json', '--db', 'sqlite:///a.db'])

    assert code == 1
    assert capsys.readouterr().err == (
        'error: result was not written to all targets\n'
    )


def test_run_failed_write_prints_retry(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = fake_api('run', FAILED_REPORT)

    code = main(
        ['run', '-b', 'nbody', '--db', 'sqlite:///a.db', '--name', 'x'],
    )

    assert code == 1
    assert fake.args == (('-b', 'nbody'),)
    assert (
        'Retry without re-running benchmarks: '
        'takt import r.json --db sqlite:///a.db --name default'
    ) in capsys.readouterr().err.splitlines()


def test_retry_keeps_rendered_name_from_any_source(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api('run', dataclasses.replace(FAILED_REPORT, name='nightly {x}'))

    code = main(['run', '-b', 'nbody', '--db', 'sqlite:///a.db'])

    assert code == 1
    assert (
        'Retry without re-running benchmarks: '
        "takt import r.json --db sqlite:///a.db --name 'nightly {{x}}'"
    ) in capsys.readouterr().err.splitlines()


def test_report_comes_before_error_in_one_log(
    fake_api: Callable[[str, object], Recorder],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_api('run', FAILED_REPORT)
    log: list[str] = []
    monkeypatch.setattr(sys, 'stdout', BufferedOutput(log))
    monkeypatch.setattr(sys, 'stderr', DirectOutput(log))

    main(['run', '-b', 'nbody', '--db', 'sqlite:///a.db'])

    assert ''.join(log).splitlines() == [
        'Result 3fa2b1c4d5e6 (default) from r.json',
        '  local: rolled back',
        '  mariadb+pymysql://u:***@h/db: failed: connection refused',
        'error: result was not written to all targets',
        (
            'Retry without re-running benchmarks: '
            'takt import r.json --db sqlite:///a.db --name default'
        ),
    ]


def test_run_partial_result_prints_import_hint(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api(
        'run',
        BenchmarkFailedError(
            'benchmark command failed with exit code 1: x',
            return_code=1,
            result_path=Path('r.json'),
        ),
    )

    code = main(
        ['run', '-b', 'nbody', '--db', 'sqlite:///a.db', '--name', 'x'],
    )

    assert code == 1
    assert capsys.readouterr().err == (
        'error: benchmark command failed with exit code 1: x\n'
        'Partial result was written to r.json. '
        'Load it without re-running benchmarks: '
        'takt import r.json --db sqlite:///a.db --name x\n'
    )


def test_run_failure_without_result_has_no_hint(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api(
        'run',
        BenchmarkFailedError(
            'cannot start benchmark command: boom',
            return_code=127,
        ),
    )

    code = main(['run', '-b', 'nbody', '--db', 'sqlite:///a.db'])

    assert code == 1
    assert capsys.readouterr().err == (
        'error: cannot start benchmark command: boom\n'
    )


def test_run_late_name_error_prints_result_path(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api(
        'run',
        InvalidRunNameError(
            "run name must not contain ':': 'a:b'",
            result_path=Path('r.json'),
        ),
    )

    code = main(['run', '-b', 'nbody', '--db', 'sqlite:///a.db'])

    assert code == 2
    assert capsys.readouterr().err == (
        "error: run name must not contain ':': 'a:b'\n"
        'Result was written to r.json. '
        'Load it with takt import and another --name.\n'
    )


def test_run_early_name_error_has_no_hint(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api('run', InvalidRunNameError('run name must not be empty'))

    code = main(['run', '-b', 'nbody', '--db', 'sqlite:///a.db'])

    assert code == 2
    assert capsys.readouterr().err == 'error: run name must not be empty\n'


def test_takt_error_exit_code(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api('import_results', ConfigurationError(NO_TARGETS))

    code = main(['import', 'r.json'])

    assert code == 2
    assert capsys.readouterr().err == f'error: {NO_TARGETS}\n'


def test_execution_error_exit_code(
    fake_api: Callable[[str, object], Recorder],
) -> None:
    fake_api(
        'compare',
        OperandNotFoundError(
            "operand 'x' not found: no file, run name or hash prefix matches",
        ),
    )

    assert main(['compare', 'x', 'y']) == 1


def test_keyboard_interrupt(
    fake_api: Callable[[str, object], Recorder],
) -> None:
    fake_api('run', KeyboardInterrupt())

    assert main(['run', '--db', 'sqlite:///a.db']) == 130


def test_keyboard_interrupt_names_partial_result(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    interrupt = KeyboardInterrupt()
    interrupt.__cause__ = BenchmarkInterruptedError(Path('r.json'))
    fake_api('run', interrupt)

    code = main(['run', 'bench.py', '--db', 'sqlite:///a.db', '--name', 'x'])

    assert code == 130
    assert capsys.readouterr().err == (
        'Partial result was written to r.json. '
        'Load it without re-running benchmarks: '
        'takt import r.json --db sqlite:///a.db --name x\n'
    )


def test_keyboard_interrupt_during_write_names_result(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    interrupt = KeyboardInterrupt()
    interrupt.__cause__ = WriteInterruptedError(Path('r.json'), 'n 2026')
    fake_api('run', interrupt)

    code = main(['run', '--db', 'sqlite:///a.db', '--name', 'n {date}'])

    assert code == 130
    assert capsys.readouterr().err == (
        'Result was written to r.json. '
        'Load it without re-running benchmarks: '
        "takt import r.json --db sqlite:///a.db --name 'n 2026'\n"
    )


def test_unknown_flag_for_import(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(['import', 'r.json', '--fast'])

    assert error.value.code == 2
    assert 'unrecognized arguments: --fast' in capsys.readouterr().err


def test_compare_writes_markdown(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    fake_api('compare', SNAPSHOT_TABLE)
    markdown = tmp_path / 'out.md'

    code = main(['compare', 'a', 'b', '--markdown', str(markdown)])

    assert code == 0
    assert markdown.read_text(encoding='utf-8') == SNAPSHOT_MARKDOWN
    assert 'Markdown table written to' in capsys.readouterr().out


def test_compare_writes_markdown_under_home(
    fake_api: Callable[[str, object], Recorder],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_api('compare', SNAPSHOT_TABLE)
    monkeypatch.setenv('HOME', str(tmp_path))

    code = main(['compare', 'a', 'b', '--markdown=~/out.md'])

    assert code == 0
    assert (tmp_path / 'out.md').read_text(encoding='utf-8') == (
        SNAPSHOT_MARKDOWN
    )


def test_compare_log_keeps_full_labels(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    labels = tuple(
        f'results/nightly/cpython-main-2026-09-{day}.json'
        for day in ('20', '21', '25')
    )
    note = f'Ignored benchmarks (1) of {labels[0]}: go'
    fake_api(
        'compare',
        CompareTable(
            headers=('Benchmark', *labels),
            rows=(('nbody', '100 ms', '90.0 ms: 1.11x faster', '1 ms'),),
            hidden_not_significant=(),
            ignored=((labels[0], ('go',)),),
        ),
    )
    monkeypatch.delenv('COLUMNS', raising=False)
    monkeypatch.setenv('FORCE_COLOR', '1')

    assert main(['compare', *labels]) == 0

    lines = plain_output(capsys).splitlines()
    assert all(label in lines[1] for label in labels)
    assert '90.0 ms: 1.11x faster' in lines[3]
    assert lines[-1] == note


def test_compare_terminal_keeps_its_width(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_api('compare', SNAPSHOT_TABLE)
    monkeypatch.setattr(sys.stdout, 'isatty', lambda: True)
    monkeypatch.setenv('COLUMNS', '30')

    assert main(['compare', 'a', 'b']) == 0

    lines = plain_output(capsys).splitlines()
    assert max(len(line) for line in lines) <= 30


def test_compare_markdown_write_error(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    fake_api('compare', SNAPSHOT_TABLE)
    markdown = tmp_path / 'missing' / 't.md'

    code = main(['compare', 'a', 'b', '--markdown', str(markdown)])

    assert code == 1
    assert capsys.readouterr().err.startswith(
        'error: cannot write markdown file',
    )


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(['--version'])

    assert error.value.code == 0
    assert capsys.readouterr().out.startswith('takt ')
