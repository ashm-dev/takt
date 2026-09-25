from takt.domain.compare.normalized_mean import format_normalized_mean


def test_no_change() -> None:
    assert format_normalized_mean(1.0) == 'no change'


def test_faster() -> None:
    assert format_normalized_mean(0.9) == '1.11x faster'


def test_slower() -> None:
    assert format_normalized_mean(1.05) == '1.05x slower'
