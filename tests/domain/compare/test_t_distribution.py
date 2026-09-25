from takt.domain.compare.t_distribution import tdist95conf_level


def test_table_values() -> None:
    assert tdist95conf_level(1) == 12.706
    assert tdist95conf_level(2) == 4.303
    assert tdist95conf_level(10) == 2.228
    assert tdist95conf_level(30) == 2.042


def test_ranges() -> None:
    assert tdist95conf_level(31) == 2.042
    assert tdist95conf_level(40) == 2.021
    assert tdist95conf_level(50) == 2.009
    assert tdist95conf_level(60) == 2.0
    assert tdist95conf_level(80) == 1.99
    assert tdist95conf_level(100) == 1.984
    assert tdist95conf_level(200) == 1.96
    assert tdist95conf_level(1000) == 1.96


def test_rounding() -> None:
    assert tdist95conf_level(9.6) == 2.228


def test_zero() -> None:
    assert tdist95conf_level(0) == 0.0
