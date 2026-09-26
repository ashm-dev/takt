import subprocess
import sys

import pytest

from takt.infrastructure.runner.takt_flags import TAKT_FLAGS
from tests.help_flags import help_flags


def _help_flags(command: tuple[str, ...]) -> set[str]:
    completed = subprocess.run(  # noqa: S603 - arguments are passed as a tuple without a shell
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    return help_flags(completed.stdout)


def test_values() -> None:
    assert TAKT_FLAGS == ('--db', '--target', '--config', '--name')


@pytest.mark.usefixtures('no_color')
def test_no_collision_with_pyperformance() -> None:
    flags = _help_flags(
        (sys.executable, '-m', 'pyperformance', 'run', '--help')
    )
    assert {'--output', '--benchmarks'} <= flags
    assert not flags.intersection(TAKT_FLAGS)


@pytest.mark.usefixtures('no_color')
def test_no_collision_with_pyperf_runner() -> None:
    flags = _help_flags(
        (
            sys.executable,
            '-c',
            'import pyperf; pyperf.Runner().argparser.print_help()',
        )
    )
    assert {'--output', '--processes'} <= flags
    assert not flags.intersection(TAKT_FLAGS)
