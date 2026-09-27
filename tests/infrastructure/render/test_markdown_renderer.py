from takt.domain.compare.compare_table import CompareTable
from takt.infrastructure.render.markdown_renderer import render_markdown

HEADERS = ('Benchmark', 'base.json', 'new.json')
"""Column headers of the rendered table."""

ROWS = (('nbody', '100 ms', '90.0 ms: 1.11x faster'),)
"""Single benchmark row of the rendered table."""

TABLE_LINES = (
    '| Benchmark | base.json | new.json              |',
    '|-----------|:---------:|:---------------------:|',
    '| nbody     | 100 ms    | 90.0 ms: 1.11x faster |',
)
"""Expected Markdown lines for ``HEADERS`` and ``ROWS``."""


def test_snapshot_single_row() -> None:
    table = CompareTable(
        headers=HEADERS,
        rows=ROWS,
        hidden_not_significant=(),
        ignored=(),
    )

    assert render_markdown(table) == '\n'.join((*TABLE_LINES, ''))


def test_snapshot_hidden_and_ignored() -> None:
    table = CompareTable(
        headers=HEADERS,
        rows=ROWS,
        hidden_not_significant=('a', 'b'),
        ignored=(('new.json', ('x',)),),
    )

    assert render_markdown(table) == '\n'.join(
        (
            *TABLE_LINES,
            '',
            'Benchmark hidden because not significant (2): a, b',
            'Ignored benchmarks (1) of new.json: x',
            '',
        ),
    )


def test_snapshot_no_rows() -> None:
    table = CompareTable(
        headers=HEADERS,
        rows=(),
        hidden_not_significant=('a',),
        ignored=(),
    )

    assert render_markdown(table) == (
        'Benchmark hidden because not significant (1): a\n'
    )


def test_pipe_in_label_and_name_stays_in_its_cell() -> None:
    table = CompareTable(
        headers=('Benchmark', 'base', 'jit|pgo'),
        rows=(('a|b', '1 ms', '2 ms: 2.00x slower'),),
        hidden_not_significant=(),
        ignored=(),
    )

    header, _, row = render_markdown(table).splitlines()

    assert header == r'| Benchmark | base | jit\|pgo           |'
    assert row == r'| a\|b      | 1 ms | 2 ms: 2.00x slower |'


def test_ignored_line_is_apart_from_the_table() -> None:
    table = CompareTable(
        headers=HEADERS,
        rows=ROWS,
        hidden_not_significant=(),
        ignored=(('jit|pgo', ('x',)),),
    )

    assert render_markdown(table) == '\n'.join(
        (
            *TABLE_LINES,
            '',
            'Ignored benchmarks (1) of jit|pgo: x',
            '',
        ),
    )
