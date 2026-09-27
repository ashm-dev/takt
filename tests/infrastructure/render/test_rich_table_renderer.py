from rich.console import Console

from takt.domain.compare.compare_table import CompareTable
from takt.infrastructure.render.rich_table_renderer import render_rich_table

HIDDEN_LINE = 'Benchmark hidden because not significant (2): a, b'
"""Line that lists the benchmarks hidden as not significant."""


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


def test_emoji_codes_stay_text() -> None:
    table = CompareTable(
        headers=('Benchmark', ':smile:'),
        rows=((':thumbs_up:', '1 ms'),),
        hidden_not_significant=(':rocket:',),
        ignored=((':smile:', (':fire:',)),),
    )

    lines = rendered(table).rstrip('\n').split('\n')

    assert ':smile:' in lines[1]
    assert ':thumbs_up:' in lines[3]
    assert lines[-2:] == [
        'Benchmark hidden because not significant (1): :rocket:',
        'Ignored benchmarks (1) of :smile:: :fire:',
    ]


def test_narrow_terminal_folds_long_label() -> None:
    label = 'results/nightly/cpython-main-2026-09-20.json'
    table = CompareTable(
        headers=('Benchmark', label),
        rows=(('nbody', '100 ms'),),
        hidden_not_significant=(),
        ignored=(),
    )
    console = Console(
        record=True,
        width=30,
        color_system=None,
        force_terminal=True,
    )

    render_rich_table(table, console)

    text = console.export_text()
    assert '…' not in text
    assert 'cpython-main' in text
