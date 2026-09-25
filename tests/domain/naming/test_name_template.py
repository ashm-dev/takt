from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.naming.name_template import NameTemplate
from takt.domain.naming.name_values import NameValues

VALUES = NameValues(
    now=datetime(2026, 9, 25, 13, 46, 1, tzinfo=UTC),
    result_path=Path('/tmp/takt-20260925T134601Z.json'),  # noqa: S108 path text
    python_version='3.14.0 (64-bit)',
    hostname='bench-host',
    suite_hash='3fa2b1c4d5e6'.ljust(64, '0'),
)


def _parse_error(text: str) -> str:
    try:
        NameTemplate.parse(text)
    except InvalidRunNameError as error:
        return str(error)
    msg = 'expected InvalidRunNameError'
    raise AssertionError(msg)


def _render_error(template: NameTemplate, values: NameValues) -> str:
    try:
        template.render(values)
    except InvalidRunNameError as error:
        return str(error)
    msg = 'expected InvalidRunNameError'
    raise AssertionError(msg)


def test_plain_text() -> None:
    template = NameTemplate.parse('default 01.01.01')

    assert template.render(VALUES) == 'default 01.01.01'


@pytest.mark.parametrize(
    ('template', 'expected'),
    [
        ('{date}', '2026-09-25'),
        ('{datetime}', '2026-09-25T13-46-01Z'),
        ('{path}', 'takt-20260925T134601Z'),
        ('{python_version}', '3.14.0 (64-bit)'),
        ('{hostname}', 'bench-host'),
        ('{hash}', '3fa2b1c4d5e6'),
    ],
)
def test_each_placeholder(template: str, expected: str) -> None:
    assert NameTemplate.parse(template).render(VALUES) == expected


def test_combined() -> None:
    template = NameTemplate.parse('ДЕФОЛТ_{date}_{path}')
    expected = 'ДЕФОЛТ_2026-09-25_takt-20260925T134601Z'

    assert template.render(VALUES) == expected


def test_non_utc_now_is_converted() -> None:
    tzinfo = timezone(timedelta(hours=3))
    now = datetime(2026, 9, 26, 1, 0, tzinfo=tzinfo)
    values = NameValues(
        now=now,
        result_path=VALUES.result_path,
        python_version=VALUES.python_version,
        hostname=VALUES.hostname,
        suite_hash=VALUES.suite_hash,
    )

    assert NameTemplate.parse('{date}').render(values) == '2026-09-25'


def test_escaped_braces() -> None:
    template = NameTemplate.parse('{{x}} {date}')

    assert template.render(VALUES) == '{x} 2026-09-25'


@pytest.mark.parametrize(
    ('filename', 'expected'),
    [
        ('res.json.gz', 'res'),
        ('res.json', 'res'),
        ('res.txt', 'res'),
        ('res', 'res'),
    ],
)
def test_path_variants(filename: str, expected: str) -> None:
    values = NameValues(
        now=VALUES.now,
        result_path=Path(f'/tmp/{filename}'),  # noqa: S108 path text
        python_version=VALUES.python_version,
        hostname=VALUES.hostname,
        suite_hash=VALUES.suite_hash,
    )

    assert NameTemplate.parse('{path}').render(values) == expected


def test_missing_values_are_unknown() -> None:
    values = NameValues(
        now=VALUES.now,
        result_path=VALUES.result_path,
        python_version=None,
        hostname='',
        suite_hash=VALUES.suite_hash,
    )

    template = NameTemplate.parse('{python_version}-{hostname}')

    assert template.render(values) == 'unknown-unknown'


def test_empty_template() -> None:
    assert _parse_error('   ') == 'run name must not be empty'


@pytest.mark.parametrize(
    ('text', 'message'),
    [
        ('a {date', "invalid name template 'a {date': unbalanced braces"),
        ('a }', "invalid name template 'a }': unbalanced braces"),
    ],
)
def test_unbalanced_braces(text: str, message: str) -> None:
    assert _parse_error(text) == message


def test_empty_placeholder() -> None:
    assert _parse_error('a {}') == (
        "invalid name template 'a {}': empty placeholder"
    )


@pytest.mark.parametrize(
    'field',
    ['user', 'date.year', 'date[0]', '0', 'Date'],
)
def test_unknown_placeholder(field: str) -> None:
    text = f'{{{field}}}'

    assert _parse_error(text) == (
        f'invalid name template {text!r}: unknown placeholder {{{field}}}'
    )


@pytest.mark.parametrize('text', ['{date:%Y}', '{date!r}'])
def test_spec_and_conversion_forbidden(text: str) -> None:
    assert _parse_error(text).endswith(
        'format spec and conversion are not allowed in {date}',
    )


def test_colon_in_literal() -> None:
    assert _parse_error('jit:pgo') == "run name must not contain ':': 'jit:pgo'"


def test_colon_from_value() -> None:
    values = NameValues(
        now=VALUES.now,
        result_path=VALUES.result_path,
        python_version=VALUES.python_version,
        hostname='a:b',
        suite_hash=VALUES.suite_hash,
    )
    template = NameTemplate.parse('{hostname}')

    assert (
        _render_error(template, values)
        == "run name must not contain ':': 'a:b'"
    )


def test_rendered_empty() -> None:
    values = NameValues(
        now=VALUES.now,
        result_path=VALUES.result_path,
        python_version=' ',
        hostname=VALUES.hostname,
        suite_hash=VALUES.suite_hash,
    )
    template = NameTemplate.parse('{python_version}')

    assert _render_error(template, values) == 'run name must not be empty'


def test_too_long() -> None:
    template = NameTemplate.parse('x' * 256)

    assert _render_error(template, VALUES) == (
        'run name must be at most 255 characters, got 256'
    )
    assert NameTemplate.parse('x' * 255).render(VALUES) == 'x' * 255
