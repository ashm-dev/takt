"""Rendering of a compare table as Markdown text."""

from collections.abc import Sequence

from takt.domain.compare.compare_table import CompareTable


def render_markdown(table: CompareTable) -> str:
    """Render the compare table like pyperf ``MarkDownTable``.

    :param table: Compare table to render.
    :returns: Markdown text ending with a newline.
    """
    lines = _table_lines(table) if table.rows else []
    hidden = table.hidden_not_significant
    if hidden:
        if table.rows:
            lines.append('')
        lines.append(_hidden_line(hidden))
    lines.extend(_ignored_line(label, names) for label, names in table.ignored)
    text = '\n'.join(lines)
    return f'{text}\n'


def _table_lines(table: CompareTable) -> list[str]:
    widths = [
        max(len(cell) for cell in column)
        for column in zip(table.headers, *table.rows, strict=True)
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


def _hidden_line(hidden: Sequence[str]) -> str:
    count = len(hidden)
    names = ', '.join(hidden)
    return f'Benchmark hidden because not significant ({count}): {names}'


def _ignored_line(label: str, names: Sequence[str]) -> str:
    count = len(names)
    joined = ', '.join(names)
    return f'Ignored benchmarks ({count}) of {label}: {joined}'
