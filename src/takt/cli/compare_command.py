"""Handler of ``takt compare``."""

import argparse
import sys

from rich.console import Console

from takt import api
from takt.cli.error_output import print_error
from takt.cli.exit_code import ExitCode
from takt.infrastructure.render.markdown_renderer import render_markdown
from takt.infrastructure.render.rich_table_renderer import render_rich_table

# Wide enough that the table and its notes never wrap in a log file.
_REDIRECTED_WIDTH = 100_000


def handle_compare(args: argparse.Namespace) -> int:
    """Print the compare table and optionally write it as Markdown.

    :param args: Parsed arguments of ``takt compare``.
    :returns: Process exit code.
    """
    table = api.compare(
        args.operands,
        db=args.db,
        target=args.target,
        config=args.config,
    )
    render_rich_table(table, _console())
    if args.markdown is not None:
        try:
            args.markdown.write_text(render_markdown(table), encoding='utf-8')
        except OSError as error:
            print_error(f'cannot write markdown file {args.markdown}: {error}')
            return ExitCode.FAILURE
        sys.stdout.write(f'Markdown table written to {args.markdown}\n')
    return ExitCode.OK


def _console() -> Console:
    console = Console()
    # Rich wraps output that is not a terminal at 80 columns, and it takes
    # a log for a terminal when FORCE_COLOR is set.
    if not sys.stdout.isatty():
        console.width = _REDIRECTED_WIDTH
    return console
