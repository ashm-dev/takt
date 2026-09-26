"""Rendering of a compare table to a Rich console."""

from rich.console import Console
from rich.table import Table
from rich.text import Text

from takt.domain.compare.compare_table import CompareTable
from takt.infrastructure.render.note_lines import note_lines


def render_rich_table(table: CompareTable, console: Console) -> None:
    """Print the compare table and its notes to the console.

    :param table: Compare table to print.
    :param console: Console that receives the output.
    """
    if table.rows:
        console.print(_rich_table(table))
    for line in note_lines(table):
        # The terminal wraps a long line itself, so a copied path stays whole.
        console.print(
            line,
            markup=False,
            highlight=False,
            emoji=False,
            soft_wrap=True,
        )


def _rich_table(table: CompareTable) -> Table:
    rich_table = Table(show_header=True)
    # Folding keeps a long label whole where ellipsis would cut the part
    # that tells the columns apart.
    rich_table.add_column(Text(table.headers[0]), overflow='fold')
    for header in table.headers[1:]:
        rich_table.add_column(Text(header), justify='right', overflow='fold')
    for row in table.rows:
        rich_table.add_row(*(Text(cell) for cell in row))
    return rich_table
