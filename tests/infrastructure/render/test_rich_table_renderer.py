from rich.console import Console

from takt.domain.compare.compare_table import CompareTable
from takt.infrastructure.render.rich_table_renderer import render_rich_table

HIDDEN_LINE = 'Benchmark hidden because not significant (2): a, b'


def rendered(table: CompareTable) -> str:
    console = Console(
        record=True,
        width=120,
        color_system=None,
        force_terminal=False,
    )
    render_rich_table(table, console)
    return console.export_text()


def test_table_contains_all_cells() -> None:
    table = CompareTable(
        headers=('Benchmark', 'base.json', 'new.json'),
        rows=(('nbody', '100 ms', '90.0 ms: 1.11x faster'),),
        hidden_not_significant=('a', 'b'),
        ignored=(('new.json', ('x',)),),
    )

    text = rendered(table)

    for cell in (
        'Benchmark',
        'base.json',
        'new.json',
        'nbody',
        '100 ms',
        '90.0 ms: 1.11x faster',
    ):
        assert cell in text
    lines = text.rstrip('\n').split('\n')
    assert lines[-2:] == [HIDDEN_LINE, 'Ignored benchmarks (1) of new.json: x']
    assert lines[-3] == ''
    assert lines[-4].strip() != ''


def test_no_rows_prints_only_hidden() -> None:
    table = CompareTable(
        headers=('Benchmark', 'base.json', 'new.json'),
        rows=(),
        hidden_not_significant=('a',),
        ignored=(),
    )

    assert rendered(table).strip() == (
        'Benchmark hidden because not significant (1): a'
    )


def test_brackets_are_not_markup() -> None:
    table = CompareTable(
        headers=('Benchmark', '[bold]x[/bold]'),
        rows=(('[red]y', '1 ms'),),
        hidden_not_significant=(),
        ignored=(),
    )

    text = rendered(table)

    assert '[bold]x[/bold]' in text
    assert '[red]y' in text
