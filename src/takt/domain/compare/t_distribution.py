"""Critical values of Student's t distribution at 95% confidence."""

from typing import Final

_TDIST95_CONF_LEVELS: Final[tuple[float, ...]] = (
    0, 12.706, 4.303, 3.182, 2.776,
    2.571, 2.447, 2.365, 2.306, 2.262,
    2.228, 2.201, 2.179, 2.16, 2.145,
    2.131, 2.12, 2.11, 2.101, 2.093,
    2.086, 2.08, 2.074, 2.069, 2.064,
    2.06, 2.056, 2.052, 2.048, 2.045,
    2.042,
)  # fmt: skip

_WideRange = tuple[int, float]

_WIDE_RANGES: Final[tuple[_WideRange, ...]] = (
    (200, 1.96),
    (100, 1.984),
    (80, 1.99),
    (60, 2.0),
    (50, 2.009),
    (40, 2.021),
    (len(_TDIST95_CONF_LEVELS), _TDIST95_CONF_LEVELS[-1]),
)


def tdist95conf_level(degrees_of_freedom: float) -> float:
    """Approximate the two-tailed 95% critical value of the t distribution.

    The table and the ranges repeat pyperf 2.10.0.

    :param degrees_of_freedom: Degrees of freedom, rounded to an integer.
    :returns: The critical value.
    """
    df = round(degrees_of_freedom)
    for lower_bound, level in _WIDE_RANGES:
        if df >= lower_bound:
            return level
    return _TDIST95_CONF_LEVELS[df]
