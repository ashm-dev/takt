"""Two-sample Student's t-test used by compare."""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from takt.domain.compare.t_distribution import tdist95conf_level


@dataclass(frozen=True, kw_only=True)
class Significance:
    """Result of the significance test.

    :ivar significant: Whether the samples differ significantly.
    :ivar t_score: The t-test score, or ``None`` when it was not computed.
    """

    significant: bool
    t_score: float | None


def is_significant(
    sample1: Sequence[float],
    sample2: Sequence[float],
) -> Significance:
    """Check whether two samples differ at 95% confidence.

    Behaviour repeats pyperf 2.10.0 ``is_significant_benchs``.

    :param sample1: Values of the base benchmark.
    :param sample2: Values of the changed benchmark.
    :returns: The test result; samples that cannot be tested count as
        significant without a score.
    """
    if len(sample1) == 1 and len(sample2) == 1:
        return Significance(significant=True, t_score=None)
    critical_value = tdist95conf_level(len(sample1) + len(sample2) - 2)
    try:
        t_score = _tscore(sample1, sample2)
    except ValueError, ZeroDivisionError, statistics.StatisticsError:
        return Significance(significant=True, t_score=None)
    return Significance(
        significant=abs(t_score) >= critical_value,
        t_score=t_score,
    )


def _pooled_sample_variance(
    sample1: Sequence[float],
    sample2: Sequence[float],
) -> float:
    deg_freedom = len(sample1) + len(sample2) - 2
    mean1 = statistics.mean(sample1)
    mean2 = statistics.mean(sample2)
    squares1 = math.fsum((value - mean1) ** 2 for value in sample1)
    squares2 = math.fsum((value - mean2) ** 2 for value in sample2)
    return (squares1 + squares2) / float(deg_freedom)


def _tscore(sample1: Sequence[float], sample2: Sequence[float]) -> float:
    if len(sample1) != len(sample2):
        msg = 'different number of values'
        raise ValueError(msg)
    error = _pooled_sample_variance(sample1, sample2) / len(sample1)
    diff = statistics.mean(sample1) - statistics.mean(sample2)
    return diff / math.sqrt(error * 2)
