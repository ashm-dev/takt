from pathlib import Path

import pytest

from takt.domain.errors.usage_error import UsageError
from takt.infrastructure.runner.runner_command import build_runner_command

PY = '/usr/bin/python3.14'
CWD = Path('/work')
OUT = Path('/work/takt-x.json')
USER_OUT = Path('/work/r.json')
PYPERFORMANCE = (PY, '-m', 'pyperformance', 'run')
DEFAULT_EXTRA = ('--output', '/work/takt-x.json')
USER_EXTRA = ('--output', '/work/r.json')


def _build(*arguments: str) -> tuple[tuple[str, ...], Path]:
    return build_runner_command(arguments, python=PY, output=OUT, cwd=CWD)


def test_pyperformance_default_output() -> None:
    command, path = _build('-b', 'nbody')
    assert command == (*PYPERFORMANCE, '-b', 'nbody', *DEFAULT_EXTRA)
    assert path == OUT


def test_pyperformance_empty_arguments() -> None:
    command, path = _build()
    assert command == (*PYPERFORMANCE, *DEFAULT_EXTRA)
    assert path == OUT


@pytest.mark.parametrize(
    'arguments',
    [
        ('-o', 'r.json'),
        ('--output', 'r.json'),
        ('--output=r.json',),
        ('-or.json',),
        ('-b', 'nbody', '-o', 'r.json', '--fast'),
    ],
)
def test_user_output_forms(arguments: tuple[str, ...]) -> None:
    command, path = _build(*arguments)
    assert command == (*PYPERFORMANCE, *arguments, *USER_EXTRA)
    assert path == USER_OUT


def test_user_output_expands_home() -> None:
    _, path = _build('-o', '~/r.json')
    assert path == Path('~/r.json').expanduser()


@pytest.mark.parametrize(
    'arguments',
    [('-o',), ('--output',), ('--output=',)],
)
def test_missing_output_value(arguments: tuple[str, ...]) -> None:
    with pytest.raises(
        UsageError,
        match=r'^option -o/--output requires a file path$',
    ):
        _build(*arguments)


def test_capital_o_is_not_output() -> None:
    command, path = _build('-O', 'table')
    assert command == (*PYPERFORMANCE, '-O', 'table', *DEFAULT_EXTRA)
    assert path == OUT


def test_script_mode() -> None:
    command, path = _build('bench.py', '--fast')
    assert command == (PY, 'bench.py', '--fast', *DEFAULT_EXTRA)
    assert path == OUT


def test_script_mode_user_output() -> None:
    command, path = _build('bench.py', '-o', 'r.json')
    assert command == (PY, 'bench.py', '-o', 'r.json', *USER_EXTRA)
    assert path == USER_OUT


def test_py_not_first_is_pyperformance() -> None:
    command, _ = _build('--fast', 'bench.py')
    assert command == (*PYPERFORMANCE, '--fast', 'bench.py', *DEFAULT_EXTRA)


def test_dash_py_is_not_script() -> None:
    command, _ = _build('-x.py')
    assert command == (*PYPERFORMANCE, '-x.py', *DEFAULT_EXTRA)
