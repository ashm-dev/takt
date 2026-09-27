"""Human-readable formatting of a benchmark value."""

from typing import Final

_TIMEDELTA_UNITS: Final[tuple[str, ...]] = ('sec', 'ms', 'us', 'ns')
"""Unit names for seconds, milliseconds, microseconds and nanoseconds."""

_MAX_POWER: Final = 2
"""Largest decimal exponent that sets the precision of a time value."""

_MIN_POWER: Final = -9
"""Decimal exponent for time values below ``1e-8``, zero included."""

_TEN: Final = 10.0
"""Base of the decimal exponent, a float so that its powers stay floats."""

_KIB: Final = 1024.0
"""Bytes in one kibibyte."""

_MIB: Final = _KIB * _KIB
"""Bytes in one mebibyte."""

_BYTES_LIMIT: Final = 10 * _KIB
"""Sizes below this many bytes are printed in bytes."""

_KIB_LIMIT: Final = 10 * _MIB
"""Sizes above this many bytes are printed in MiB instead of KiB."""

_POW10_START: Final = 10000
"""Smallest integer value that may be printed as a power of ten."""

_POW2_START: Final = 8192
"""Integer values above this may be printed as a power of two."""


def format_value(unit: str, value: float) -> str:
    """Format one value in its pyperf unit.

    Behaviour repeats pyperf 2.10.0 ``format_value``.

    :param unit: pyperf unit: ``second``, ``byte`` or ``integer``.
    :param value: The value to format.
    :returns: The formatted value.
    :raises ValueError: If the unit is unknown.
    """
    if unit == 'second':
        return _format_timedelta(value)
    if unit == 'byte':
        return _format_filesize(value)
    if unit == 'integer':
        return _format_number(value)
    msg = f'unknown unit: {unit}'
    raise ValueError(msg)


def _format_timedelta(value: float) -> str:
    exponent = _decimal_exponent(abs(value))
    precision = 2 - exponent % 3
    scale = -(exponent // 3) if exponent < 0 else 0
    scaled = format(value * _TEN ** (scale * 3), f'.{precision}f')
    return f'{scaled} {_TIMEDELTA_UNITS[scale]}'


def _decimal_exponent(ref_value: float) -> int:
    for power in range(_MAX_POWER, _MIN_POWER, -1):
        if ref_value >= _TEN**power:
            return power
    return _MIN_POWER


def _format_filesize(value: float) -> str:
    if value < _BYTES_LIMIT:
        noun = 'byte' if value == 1 else 'bytes'
        return f'{value:.0f} {noun}'
    if value > _KIB_LIMIT:
        mebibytes = value / _MIB
        return f'{mebibytes:.1f} MiB'
    kibibytes = value / _KIB
    return f'{kibibytes:.1f} KiB'


def _format_number(value: float) -> str:
    if value >= _POW10_START:
        pow10 = _exponent(value, 10)
        if pow10 is not None:
            return f'10^{pow10}'
    if isinstance(value, int) and value > _POW2_START:
        pow2 = _exponent(value, 2)
        if pow2 is not None:
            return f'2^{pow2}'
    return str(value)


def _exponent(value: float, base: int) -> int | None:
    exponent = 0
    quotient = value
    while quotient >= base:
        quotient, remainder = divmod(quotient, base)
        exponent += 1
        if remainder:
            return None
    return exponent
