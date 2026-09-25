import math

import pytest

from takt.domain.compare.significance import Significance, is_significant


def test_single_values_are_significant() -> None:
    assert is_significant([1.0], [2.0]) == Significance(
        significant=True,
        t_score=None,
    )


def test_different_lengths_are_significant_without_score() -> None:
    assert is_significant([1.0, 2.0], [1.0, 2.0, 3.0]) == Significance(
        significant=True,
        t_score=None,
    )


def test_zero_variance_equal_means() -> None:
    assert is_significant([1.0, 1.0], [1.0, 1.0]) == Significance(
        significant=True,
        t_score=None,
    )


def test_clear_difference() -> None:
    significance = is_significant([1.0, 1.1, 0.9, 1.0], [2.0, 2.1, 1.9, 2.0])

    assert significance.significant is True
    assert significance.t_score is not None
    assert significance.t_score < 0
    assert abs(significance.t_score) > 3.182


def test_no_difference() -> None:
    significance = is_significant([1.0, 2.0, 1.0, 2.0], [2.0, 1.0, 2.0, 1.0])

    assert significance.significant is False
    assert significance.t_score == 0.0


def test_matches_formula() -> None:
    pooled = (2.0 + 2.0) / 4
    expected = (2.0 - 3.0) / math.sqrt(pooled / 3 * 2)

    significance = is_significant([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])

    assert significance.t_score == pytest.approx(expected)
    assert significance.significant is False
