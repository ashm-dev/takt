"""Rendering of a compare table as Markdown text."""

from collections.abc import Sequence

from takt.domain.compare.compare_table import CompareTable
from takt.infrastructure.render.note_lines import note_lines


def render_markdown(table: CompareTable) -> str:
    """Render the compare table like pyperf ``MarkDownTable``.

    :param table: Compare table to render.
    :returns: Markdown text ending with a newline.
    """
    lines = _table_lines(table) if table.rows else []
    lines.extend(note_lines(table))
    text = '\n'.join(lines)
    return f'{text}\n'


def _table_lines(table: CompareTable) -> list[str]:
    lines = (table.headers, *table.rows)
    widths = [
        max(len(line[column]) for line in lines)
        for column in range(len(table.headers))
    ]
    separator = [
        '-' * (widths[0] + 2),
        *(_centered_rule(width) for width in widths[1:]),
    ]
    return [
        _cells_line(table.headers, widths),
        _join(separator),
        *(_cells_line(row, widths) for row in table.rows),
    ]


def _cells_line(cells: Sequence[str], widths: Sequence[int]) -> str:
    return _join(
        [
            f' {cell.ljust(width)} '
            for cell, width in zip(cells, widths, strict=True)
        ],
    )


def _centered_rule(width: int) -> str:
    dashes = '-' * width
    return f':{dashes}:'


def _join(parts: Sequence[str]) -> str:
    joined = '|'.join(parts)
    return f'|{joined}|'
