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
    notes = note_lines(table)
    # Markdown reads a line right under a table as one more table row.
    if lines and notes and notes[0]:
        lines.append('')
    lines.extend(notes)
    text = '\n'.join(lines)
    return f'{text}\n'


def _table_lines(table: CompareTable) -> list[str]:
    # A bare | in a run name or path would start a new column.
    header, *rows = [
        [cell.replace('|', r'\|') for cell in line]
        for line in (table.headers, *table.rows)
    ]
    widths = [
        max(len(line[column]) for line in (header, *rows))
        for column in range(len(header))
    ]
    separator = [
        '-' * (widths[0] + 2),
        *(_centered_rule(width) for width in widths[1:]),
    ]
    return [
        _cells_line(header, widths),
        _join(separator),
        *(_cells_line(row, widths) for row in rows),
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
