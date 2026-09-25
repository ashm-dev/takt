"""Rendering of a compare table to a Rich console."""

from collections.abc import Sequence

from rich.console import Console
from rich.table import Table
from rich.text import Text

from takt.domain.compare.compare_table import CompareTable


def render_rich_table(table: CompareTable, console: Console) -> None:
    """Print the compare table and its notes to the console.

    :param table: Compare table to print.
    :param console: Console that receives the output.
    """
    if table.rows:
        console.print(_rich_table(table))
    hidden = table.hidden_not_significant
    if hidden:
        if table.rows:
            console.print()
        _print_plain(console, _hidden_line(hidden))
    for label, names in table.ignored:
        _print_plain(console, _ignored_line(label, names))


def _rich_table(table: CompareTable) -> Table:
    rich_table = Table(show_header=True)
    rich_table.add_column(Text(table.headers[0]), justify='left')
    for header in table.headers[1:]:
        rich_table.add_column(Text(header), justify='right')
    for row in table.rows:
        rich_table.add_row(*(Text(cell) for cell in row))
    return rich_table


def _print_plain(console: Console, line: str) -> None:
    console.print(line, markup=False, highlight=False)


def _hidden_line(hidden: Sequence[str]) -> str:
    count = len(hidden)
    names = ', '.join(hidden)
    return f'Benchmark hidden because not significant ({count}): {names}'


def _ignored_line(label: str, names: Sequence[str]) -> str:
    count = len(names)
    joined = ', '.join(names)
    return f'Ignored benchmarks ({count}) of {label}: {joined}'
