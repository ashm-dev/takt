"""Command line of pyperformance or a pyperf script."""

from pathlib import Path

from takt.domain.errors.usage_error import UsageError

_MISSING_OUTPUT = 'option -o/--output requires a file path'
_OUTPUT_FLAGS = frozenset(('-o', '--output'))
_OUTPUT_PREFIX = '--output='


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
    chosen = output if user_output is None else Path(user_output).expanduser()
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
    for index, element in enumerate(arguments):
        value = _output_value(element, arguments[index + 1 : index + 2])
        if value is not None:
            return value
    return None


def _output_value(element: str, following: tuple[str, ...]) -> str | None:
    if element in _OUTPUT_FLAGS:
        if not following:
            raise UsageError(_MISSING_OUTPUT)
        return following[0]
    if element.startswith(_OUTPUT_PREFIX):
        value = element.removeprefix(_OUTPUT_PREFIX)
        if not value:
            raise UsageError(_MISSING_OUTPUT)
        return value
    if element.startswith('-o') and not element.startswith('--'):
        return element[2:]
    return None
