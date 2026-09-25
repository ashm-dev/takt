import pytest

from takt.domain.compare.value_format import format_value


@pytest.mark.parametrize(
    ('unit', 'value', 'expected'),
    [
        ('second', 0.1, '100 ms'),
        ('second', 0.09, '90.0 ms'),
        ('second', 0.0012345, '1.23 ms'),
        ('second', 1.5, '1.50 sec'),
        ('second', 123.4, '123 sec'),
        ('second', 0.0000123, '12.3 us'),
        ('second', 5e-10, '0.50 ns'),
        ('byte', 1, '1 byte'),
        ('byte', 500, '500 bytes'),
        ('byte', 20480, '20.0 KiB'),
        ('byte', 20971520, '20.0 MiB'),
        ('integer', 123.5, '123.5'),
        ('integer', 100000.0, '10^5'),
        ('integer', 12345.0, '12345.0'),
    ],
)
def test_format_value(unit: str, value: float, expected: str) -> None:
    assert format_value(unit, value) == expected


def test_unknown_unit() -> None:
    with pytest.raises(ValueError, match='unknown unit: meter'):
        format_value('meter', 1.0)
