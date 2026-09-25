"""Entry point of the takt command."""

import argparse
from collections.abc import Sequence

from takt.cli.compare_command import handle_compare
from takt.cli.error_output import print_error
from takt.cli.exit_code import ExitCode
from takt.cli.import_command import handle_import
from takt.cli.parser import build_parser
from takt.cli.run_command import handle_run
from takt.domain.errors.takt_error import TaktError


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, run the command and return the exit code.

    Only ``takt run`` accepts unknown arguments: they go to pyperformance
    or the pyperf script unchanged.

    :param argv: Arguments without the program name; ``sys.argv`` if
        ``None``.
    :returns: Process exit code.
    """
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)
    if args.command != 'run' and extra:
        unknown = ' '.join(extra)
        parser.error(f'unrecognized arguments: {unknown}')
    try:
        return _dispatch(args, tuple(extra))
    except TaktError as error:
        print_error(str(error))
        return error.exit_code
    except KeyboardInterrupt:
        return ExitCode.INTERRUPTED


def _dispatch(args: argparse.Namespace, extra: tuple[str, ...]) -> int:
    if args.command == 'run':
        return handle_run(args, extra)
    if args.command == 'import':
        return handle_import(args)
    return handle_compare(args)
