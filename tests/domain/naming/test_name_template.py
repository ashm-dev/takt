import dataclasses
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from tests.domain.exact_pattern import exact_pattern

from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.naming.name_template import NameTemplate
from takt.domain.naming.name_values import NameValues

VALUES = NameValues(
    now=datetime(2026, 9, 25, 13, 46, 1, tzinfo=UTC),
    result_path=Path('results/takt-20260925T134601Z.json'),
    python_version='3.14.0 (64-bit)',
    hostname='bench-host',
    suite_hash='3fa2b1c4d5e6'.ljust(64, '0'),
)


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
    values = dataclasses.replace(VALUES, now=now)

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
    values = dataclasses.replace(
        VALUES,
        result_path=Path(f'results/{filename}'),
    )

    assert NameTemplate.parse('{path}').render(values) == expected


def test_missing_values_are_unknown() -> None:
    values = dataclasses.replace(VALUES, python_version=None, hostname='')

    template = NameTemplate.parse('{python_version}-{hostname}')

    assert template.render(values) == 'unknown-unknown'


def test_empty_template() -> None:
    with pytest.raises(
        InvalidRunNameError,
        match=exact_pattern('run name must not be empty'),
    ):
        NameTemplate.parse('   ')


@pytest.mark.parametrize(
    ('text', 'message'),
    [
        ('a {date', "invalid name template 'a {date': unbalanced braces"),
        ('a }', "invalid name template 'a }': unbalanced braces"),
    ],
)
def test_unbalanced_braces(text: str, message: str) -> None:
    with pytest.raises(InvalidRunNameError, match=exact_pattern(message)):
        NameTemplate.parse(text)


def test_empty_placeholder() -> None:
    with pytest.raises(
        InvalidRunNameError,
        match=exact_pattern("invalid name template 'a {}': empty placeholder"),
    ):
        NameTemplate.parse('a {}')


@pytest.mark.parametrize(
    'field',
    ['user', 'date.year', 'date[0]', '0', 'Date'],
)
def test_unknown_placeholder(field: str) -> None:
    text = f'{{{field}}}'
    message = f'invalid name template {text!r}: unknown placeholder {{{field}}}'

    with pytest.raises(InvalidRunNameError, match=exact_pattern(message)):
        NameTemplate.parse(text)


@pytest.mark.parametrize('text', ['{date:%Y}', '{date!r}'])
def test_spec_and_conversion_forbidden(text: str) -> None:
    message = (
        f'invalid name template {text!r}: format spec and conversion '
        'are not allowed in {date}'
    )

    with pytest.raises(InvalidRunNameError, match=exact_pattern(message)):
        NameTemplate.parse(text)


def test_colon_in_literal() -> None:
    with pytest.raises(
        InvalidRunNameError,
        match=exact_pattern("run name must not contain ':': 'jit:pgo'"),
    ):
        NameTemplate.parse('jit:pgo')


def test_colon_from_value() -> None:
    values = dataclasses.replace(VALUES, hostname='a:b')
    template = NameTemplate.parse('{hostname}')

    with pytest.raises(
        InvalidRunNameError,
        match=exact_pattern("run name must not contain ':': 'a:b'"),
    ):
        template.render(values)


def test_rendered_empty() -> None:
    values = dataclasses.replace(VALUES, python_version=' ')
    template = NameTemplate.parse('{python_version}')

    with pytest.raises(
        InvalidRunNameError,
        match=exact_pattern('run name must not be empty'),
    ):
        template.render(values)


def test_too_long() -> None:
    template = NameTemplate.parse('x' * 256)

    with pytest.raises(
        InvalidRunNameError,
        match=exact_pattern('run name must be at most 255 characters, got 256'),
    ):
        template.render(VALUES)
    assert NameTemplate.parse('x' * 255).render(VALUES) == 'x' * 255
