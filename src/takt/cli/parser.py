"""Argument parser of the takt command."""

import argparse
from pathlib import Path

from takt import __version__
from takt.infrastructure.runner.takt_flags import (
    CONFIG_FLAG,
    DB_FLAG,
    NAME_FLAG,
    TARGET_FLAG,
)

_RUN_USAGE = (
    'takt run [takt flags] [pyperformance run flags ...]\n'
    '       takt run SCRIPT.py [takt flags] [pyperf.Runner flags ...]'
)
_RUN_DESCRIPTION = (
    'Run benchmarks and store the result in every selected database.\n\n'
    'Every argument that is not a takt flag goes unchanged to\n'
    "'python -m pyperformance run', for example -b nbody --fast; without\n"
    'such arguments the whole pyperformance suite runs.\n'
    'If the first of them ends in .py, it is a pyperf.Runner script, and\n'
    'takt runs it with the other arguments.\n'
    '-o/--output picks the result file; the default is\n'
    './takt-<UTC time>.json.'
)
_RUN_EPILOG = (
    '--help always shows this help. The flags of the runner itself are\n'
    "shown by 'python -m pyperformance run --help' or\n"
    "'python SCRIPT.py --help'.\n\n"
    'examples:\n'
    '  takt run -b nbody --fast --db sqlite:///bench.db\n'
    '  takt run bench_sort.py --values 5 --db sqlite:///bench.db'
)
_OPERAND_HELP = (
    'Result file (.json or .json.gz), run name, NAME:N (N-th run with '
    'that name, from 0, by date), NAME:HASH_PREFIX or a hash prefix of '
    'at least 6 lowercase hex characters. Give two or more; the first one '
    'is the base.'
)
_REPEATABLE = 'repeatable'


def build_parser() -> argparse.ArgumentParser:
    """Build the parser for ``takt run``, ``takt import`` and ``compare``.

    Abbreviations are disabled everywhere so that pyperformance flags like
    ``--tags`` are never taken for ``--target``.

    :returns: The root parser with its subcommands.
    """
    parser = argparse.ArgumentParser(
        prog='takt',
        description=(
            'Run pyperformance/pyperf benchmarks and store results in '
            'databases.'
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'takt {__version__}',
    )
    commands = parser.add_subparsers(dest='command', required=True)
    _add_run(commands)
    _add_import(commands)
    _add_compare(commands)
    return parser


def _add_run(
    commands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    run = commands.add_parser(
        'run',
        help='Run benchmarks and store the result.',
        usage=_RUN_USAGE,
        description=_RUN_DESCRIPTION,
        epilog=_RUN_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    _add_target_flags(run, _REPEATABLE)
    _add_name_flag(run)


def _add_import(
    commands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    import_parser = commands.add_parser(
        'import',
        help='Store an existing pyperf/pyperformance JSON result.',
        allow_abbrev=False,
    )
    import_parser.add_argument(
        'path',
        type=Path,
        metavar='PATH',
        help='pyperf or pyperformance JSON result (.json or .json.gz).',
    )
    _add_target_flags(import_parser, _REPEATABLE)
    _add_name_flag(import_parser)


def _add_compare(
    commands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    compare = commands.add_parser(
        'compare',
        help='Compare results from files and databases.',
        allow_abbrev=False,
    )
    compare.add_argument(
        'operands',
        nargs='+',
        metavar='OPERAND',
        help=_OPERAND_HELP,
    )
    _add_target_flags(compare, 'only the first target is read')
    compare.add_argument(
        '--markdown',
        type=Path,
        default=None,
        metavar='PATH',
        help='Also write the table as Markdown to PATH.',
    )


def _add_target_flags(parser: argparse.ArgumentParser, note: str) -> None:
    parser.add_argument(
        DB_FLAG,
        action='append',
        default=[],
        metavar='URL',
        help=f'SQLAlchemy URL of a target database ({note}).',
    )
    parser.add_argument(
        TARGET_FLAG,
        action='append',
        default=[],
        metavar='NAME',
        help=f'Named target from takt.toml ({note}).',
    )
    parser.add_argument(
        CONFIG_FLAG,
        type=Path,
        default=None,
        metavar='PATH',
        help='Path to takt.toml.',
    )


def _add_name_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        NAME_FLAG,
        default=None,
        metavar='TEMPLATE',
        help='Run name or name template.',
    )
