"""Command line of pyperformance or a pyperf script."""

import argparse
from pathlib import Path

from takt.domain.errors.usage_error import UsageError
from takt.domain.operand.expand_home import expand_home

_MISSING_OUTPUT = 'option -o/--output requires a file path'
"""Error text for ``-o`` or ``--output`` without a path."""

_OUTPUT_OPTION = '-o/--output'
"""Name that argparse gives the output option in its errors."""

_SWITCHES = ('-d', '-f', '-g', '-m', '-q', '-r', '-t', '-v')
"""Flags without a value, so ``-fo FILE`` reads as ``-f -o FILE``."""


def build_runner_command(
    arguments: tuple[str, ...],
    *,
    python: str,
    output: Path,
    cwd: Path,
) -> tuple[tuple[str, ...], Path]:
    """Build the benchmark command and find its result file.

    The result path goes as ``--output`` after the other options and
    before a ``--`` separator: pyperformance and ``pyperf.Runner`` keep
    the last value, so takt and the child process agree on the file
    whatever form of the option the user wrote.

    :param arguments: Arguments of ``takt run`` without takt flags.
    :param python: Interpreter that runs the benchmarks.
    :param output: Result path used when ``arguments`` have no ``-o``.
    :param cwd: Directory that a relative result path is resolved against.
    :returns: Command and absolute path to the result file.
    :raises UsageError: If ``-o``/``--output`` has no value.
    """
    user_output = _find_output(arguments)
    chosen = output if user_output is None else expand_home(user_output)
    result_path = cwd / chosen
    options = _with_output(arguments, result_path)
    if _is_script(arguments):
        return (python, *options), result_path
    return (python, '-m', 'pyperformance', 'run', *options), result_path


def _with_output(
    arguments: tuple[str, ...],
    result_path: Path,
) -> tuple[str, ...]:
    # Everything after ``--`` is a positional argument of the runner.
    end = arguments.index('--') if '--' in arguments else len(arguments)
    extra = ('--output', str(result_path))
    return (*arguments[:end], *extra, *arguments[end:])


def _is_script(arguments: tuple[str, ...]) -> bool:
    if not arguments:
        return False
    first = arguments[0]
    return not first.startswith('-') and first.endswith('.py')


def _find_output(arguments: tuple[str, ...]) -> str | None:
    parser = argparse.ArgumentParser(
        prog='takt run',
        add_help=False,
        allow_abbrev=True,
        exit_on_error=False,
    )
    parser.add_argument('-o', '--output')
    for switch in _SWITCHES:
        parser.add_argument(switch, action='store_true')
    try:
        namespace, _ = parser.parse_known_args(arguments)
    except argparse.ArgumentError as exc:
        if exc.argument_name != _OUTPUT_OPTION:
            # The runner itself rejects a flag with a value, such as -f=x.
            return None
        raise UsageError(_MISSING_OUTPUT) from exc
    user_output: str | None = namespace.output
    if user_output == '':
        raise UsageError(_MISSING_OUTPUT)
    return user_output
