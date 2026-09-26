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
        allow_abbrev=False,
    )
    _add_target_flags(run)
    _add_name_flag(run)


def _add_import(
    commands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    import_parser = commands.add_parser(
        'import',
        help='Store an existing pyperf/pyperformance JSON result.',
        allow_abbrev=False,
    )
    import_parser.add_argument('path', type=Path, metavar='PATH')
    _add_target_flags(import_parser)
    _add_name_flag(import_parser)


def _add_compare(
    commands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    compare = commands.add_parser(
        'compare',
        help='Compare results from files and databases.',
        allow_abbrev=False,
    )
    compare.add_argument('operands', nargs='+', metavar='OPERAND')
    _add_target_flags(compare)
    compare.add_argument(
        '--markdown',
        type=Path,
        default=None,
        metavar='PATH',
        help='Also write the table as Markdown to PATH.',
    )


def _add_target_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        DB_FLAG,
        action='append',
        default=[],
        metavar='URL',
        help='SQLAlchemy URL of a target database (repeatable).',
    )
    parser.add_argument(
        TARGET_FLAG,
        action='append',
        default=[],
        metavar='NAME',
        help='Named target from takt.toml (repeatable).',
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
