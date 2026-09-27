import sys
from pathlib import Path

import pytest

from takt.domain.errors.usage_error import UsageError
from takt.infrastructure.runner.runner_command import build_runner_command

PY = '/usr/bin/python3.14'
"""Python interpreter path passed to the command builder."""

CWD = Path('/work')
"""Working folder that relative output paths resolve against."""

OUT = Path('/work/takt-x.json')
"""Default output path used when the user gives none."""

USER_OUT = Path('/work/r.json')
"""Output path that the user gives as ``r.json``."""

PYPERFORMANCE = (PY, '-m', 'pyperformance', 'run')
"""Command start for a pyperformance run."""

DEFAULT_EXTRA = ('--output', '/work/takt-x.json')
"""Output flag added for the default output path."""

USER_EXTRA = ('--output', '/work/r.json')
"""Output flag added for the user output path."""


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
        ('-or.json',),
        ('-o=r.json',),
        ('--output', 'r.json'),
        ('--output=r.json',),
        ('--out', 'r.json'),
        ('-b', 'nbody', '-o', 'r.json', '--fast'),
        ('-vfor.json',),
        ('-qo=r.json',),
    ],
)
def test_user_output_forms(arguments: tuple[str, ...]) -> None:
    command, path = _build(*arguments)
    assert command == (*PYPERFORMANCE, *arguments, *USER_EXTRA)
    assert path == USER_OUT


def test_output_goes_before_double_dash() -> None:
    tail = ('--', '-o', 'x')
    command = (PY, 'bench.py', '-o', 'r.json', *USER_EXTRA, *tail)
    assert _build('bench.py', '-o', 'r.json', *tail) == (command, USER_OUT)


def test_output_after_double_dash_is_not_read() -> None:
    tail = ('--', '-o', 'x')
    command = (*PYPERFORMANCE, '-b', 'nbody', *DEFAULT_EXTRA, *tail)
    assert _build('-b', 'nbody', *tail) == (command, OUT)


def test_output_in_short_flag_cluster() -> None:
    command = (*PYPERFORMANCE, '-fo', 'r.json', *USER_EXTRA)
    assert _build('-fo', 'r.json') == (command, USER_OUT)


def test_flag_with_value_keeps_default_output() -> None:
    command = (*PYPERFORMANCE, '-f=x', *DEFAULT_EXTRA)
    assert _build('-f=x') == (command, OUT)


@pytest.mark.parametrize(
    'arguments',
    [('-o', '~/r.json'), ('--output=~/r.json',)],
)
def test_user_output_expands_home(arguments: tuple[str, ...]) -> None:
    command, path = _build(*arguments)
    expanded = Path('~/r.json').expanduser()
    assert path == expanded
    assert command[-2:] == ('--output', str(expanded))


def test_unknown_user_output_is_kept() -> None:
    arguments = ('-o', '~takt_no_such_user/r.json')
    kept = CWD / '~takt_no_such_user/r.json'
    command = (*PYPERFORMANCE, *arguments, '--output', str(kept))
    assert _build(*arguments) == (command, kept)


@pytest.mark.parametrize(
    'arguments',
    [('-o',), ('--output',), ('--output=',), ('-fo',)],
)
def test_missing_output_value(arguments: tuple[str, ...]) -> None:
    with pytest.raises(
        UsageError,
        match=r'^option -o/--output requires a file path$',
    ):
        _build(*arguments)


def test_output_without_sys_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(sys, 'argv')
    command = (*PYPERFORMANCE, '-o', 'r.json', *USER_EXTRA)
    assert _build('-o', 'r.json') == (command, USER_OUT)


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
