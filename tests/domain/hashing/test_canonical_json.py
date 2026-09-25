import math

import pytest

from takt.domain.hashing.canonical_json import canonical_json


def test_canonical_json_sorts_keys_and_drops_spaces() -> None:
    document = {'b': 1, 'a': [1, 2]}

    assert canonical_json(document) == b'{"a":[1,2],"b":1}'


def test_canonical_json_sorts_nested_keys() -> None:
    document = {'z': {'y': 1, 'x': 2}}

    assert canonical_json(document) == b'{"z":{"x":2,"y":1}}'


def test_canonical_json_keeps_unicode_as_utf8() -> None:
    document = {'name': 'ж', 'value': 1.5}

    assert canonical_json(document) == (b'{"name":"\xd0\xb6","value":1.5}')


def test_canonical_json_keeps_float_repr() -> None:
    assert canonical_json({'a': 1.0}) == b'{"a":1.0}'
    assert canonical_json({'a': 1e-7}) == b'{"a":1e-07}'


@pytest.mark.parametrize('number', [math.nan, math.inf, -math.inf])
def test_canonical_json_rejects_non_finite_numbers(number: float) -> None:
    with pytest.raises(ValueError, match='Out of range float values'):
        canonical_json({'a': number})


def test_canonical_json_rejects_unsupported_types() -> None:
    with pytest.raises(TypeError, match='is not JSON serializable'):
        canonical_json({'a': {1, 2}})
