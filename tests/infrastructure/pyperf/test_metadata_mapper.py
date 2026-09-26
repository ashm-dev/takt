import dataclasses
from types import MappingProxyType

import pytest

from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.infrastructure.pyperf import metadata_mapper
from takt.infrastructure.pyperf.metadata_mapper import (
    to_run_metadata as map_metadata,
)


def test_known_keys_go_to_fields() -> None:
    metadata = map_metadata(
        {
            'name': 'x',
            'loops': 3,
            'duration': 1.5,
            'cpu_count': 8,
            'hostname': 'h',
        }
    )

    assert metadata.name == 'x'
    assert metadata.loops == 3
    assert metadata.duration == 1.5
    assert metadata.cpu_count == 8
    assert metadata.hostname == 'h'
    assert metadata.custom == {}


def test_type_mismatch_goes_to_custom() -> None:
    raw = {'duration': 2, 'loops': 2.5, 'cpu_count': '8', 'inner_loops': True}

    metadata = map_metadata(raw)

    assert metadata.duration is None
    assert metadata.loops is None
    assert metadata.cpu_count is None
    assert metadata.inner_loops is None
    assert metadata.custom == raw


def test_hash_seed_int_becomes_str() -> None:
    metadata = map_metadata({'python_hash_seed': 0})

    assert metadata.python_hash_seed == '0'
    assert metadata.custom == {}


def test_tags_list_becomes_tuple() -> None:
    metadata = map_metadata({'tags': ['a', 'b']})

    assert metadata.tags == ('a', 'b')


def test_tuple_field_type_comes_from_key_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        metadata_mapper,
        'METADATA_KEY_TYPES',
        MappingProxyType({'python_gc': tuple}),
    )

    metadata = map_metadata({'python_gc': ['a']})

    assert dataclasses.asdict(metadata)['python_gc'] == ('a',)
    assert metadata.custom == {}


def test_custom_list_of_str_becomes_tuple() -> None:
    metadata = map_metadata({'labels': ['a']})

    assert metadata.custom == {'labels': ('a',)}


def test_unsupported_value_type_raises() -> None:
    with pytest.raises(InvalidResultError) as error:
        map_metadata({'extra': {'a': 1}})

    assert str(error.value) == (
        "unsupported metadata value type for 'extra': dict"
    )
