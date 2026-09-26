"""Note lines printed after a compare table."""

from collections.abc import Sequence

from takt.domain.compare.compare_table import CompareTable


def note_lines(table: CompareTable) -> list[str]:
    """Build the lines that follow the compare table in every renderer.

    :param table: Compare table whose notes are built.
    :returns: An empty line when rows and hidden benchmarks are both
        present, the hidden benchmarks line, then one line per operand
        with ignored benchmarks.
    """
    lines: list[str] = []
    hidden = table.hidden_not_significant
    if hidden:
        if table.rows:
            lines.append('')
        lines.append(_hidden_line(hidden))
    lines.extend(_ignored_line(label, names) for label, names in table.ignored)
    return lines


def _hidden_line(hidden: Sequence[str]) -> str:
    count = len(hidden)
    names = ', '.join(hidden)
    return f'Benchmark hidden because not significant ({count}): {names}'


def _ignored_line(label: str, names: Sequence[str]) -> str:
    count = len(names)
    joined = ', '.join(names)
    return f'Ignored benchmarks ({count}) of {label}: {joined}'
