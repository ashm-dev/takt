import json

from takt.domain.hashing.result_hash import result_hash

SORTED_HASH = '94a786c3662bc7beeb598efa7d8cb58d7bea25d6c275ea9785a0230ff1f8c2ba'
CHANGED_HASH = (
    '68b7e88ecdcf999e2736835f0354c02ff937e5c4222e67f38d1fa2682a5c15aa'
)
PYPERF_HASH = '3b6aeb6c9e41c73160b194397ff641c40653fb0686c61824eef138712dcef5f5'


def test_result_hash_matches_reference_value() -> None:
    assert result_hash({'b': 1, 'a': [1, 2]}) == SORTED_HASH


def test_result_hash_ignores_key_order() -> None:
    assert result_hash({'a': [1, 2], 'b': 1}) == SORTED_HASH


def test_result_hash_ignores_formatting() -> None:
    compact = json.loads('{"a":[1,2],"b":1}')
    indented = json.loads('{\n  "b": 1,\n  "a": [\n    1,\n    2\n  ]\n}')

    assert result_hash(compact) == result_hash(indented) == SORTED_HASH


def test_result_hash_changes_with_any_value() -> None:
    assert result_hash({'b': 2, 'a': [1, 2]}) == CHANGED_HASH


def test_result_hash_of_pyperf_document() -> None:
    document = {
        'version': '1.0',
        'benchmarks': [{'runs': [{'values': [0.1, 0.2]}]}],
    }

    assert result_hash(document) == PYPERF_HASH


def test_result_hash_is_lowercase_hex() -> None:
    digest = result_hash({})

    assert len(digest) == 64
    assert digest == digest.lower()
    assert set(digest) <= set('0123456789abcdef')
