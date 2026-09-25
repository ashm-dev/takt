"""Mapping of raw pyperf metadata to ``RunMetadata``."""

import copy
from collections.abc import Mapping
from typing import Final, TypeIs

from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.domain.model.metadata_value import MetadataValue
from takt.domain.model.run_metadata import RunMetadata

_INT_KEYS: Final[frozenset[str]] = frozenset(
    (
        'loops',
        'inner_loops',
        'calibrate_loops',
        'recalibrate_loops',
        'calibrate_warmups',
        'recalibrate_warmups',
        'mem_max_rss',
        'command_max_rss',
        'mem_peak_pagefile_usage',
        'cpu_count',
        'runnable_threads',
        'timeit_duplicate',
    )
)
_FLOAT_KEYS: Final[frozenset[str]] = frozenset(
    (
        'duration',
        'uptime',
        'load_avg_1min',
    )
)
_STR_KEYS: Final[frozenset[str]] = frozenset(
    (
        'name',
        'unit',
        'date',
        'timer',
        'description',
        'python_version',
        'python_implementation',
        'python_executable',
        'python_compiler',
        'python_cflags',
        'python_config_args',
        'python_hash_seed',
        'python_gc',
        'cpu_affinity',
        'cpu_config',
        'cpu_freq',
        'cpu_machine',
        'cpu_model_name',
        'cpu_temp',
        'aslr',
        'hostname',
        'platform',
        'boot_time',
        'perf_version',
        'performance_version',
        'timeit_stmt',
        'timeit_setup',
        'timeit_teardown',
        'commit_id',
        'commit_branch',
        'commit_date',
        'patch_file',
        'hooks',
    )
)


def to_run_metadata(metadata: Mapping[str, object]) -> RunMetadata:
    """Split raw metadata into known fields and custom keys.

    A known key goes to its field only when its value has exactly the field
    type; otherwise it goes to ``custom`` with the unknown keys.

    :param metadata: Full metadata of one run.
    :returns: Metadata with known fields filled and the rest in ``custom``.
    :raises InvalidResultError: If a value has a type that metadata cannot
        hold.
    """
    fields: dict[str, MetadataValue] = {}
    custom: dict[str, MetadataValue] = {}
    for key, value in metadata.items():
        field_value = _field_value(key, value)
        if field_value is None:
            custom[key] = _custom_value(key, value)
        else:
            fields[key] = field_value
    return copy.replace(RunMetadata(custom=custom), **fields)


def _field_value(key: str, value: object) -> MetadataValue | None:
    if key == 'tags':
        return _string_tuple(value)
    if isinstance(value, bool):
        return None
    if key == 'python_hash_seed' and isinstance(value, int):
        return str(value)
    if _is_field_type(value, key):
        return value
    return None


def _is_field_type(value: object, key: str) -> TypeIs[int | float | str]:
    return (
        (key in _INT_KEYS and isinstance(value, int))
        or (key in _FLOAT_KEYS and isinstance(value, float))
        or (key in _STR_KEYS and isinstance(value, str))
    )


def _custom_value(key: str, value: object) -> MetadataValue:
    if isinstance(value, (str, int, float)):
        return value
    strings = _string_tuple(value)
    if strings is None:
        type_name = type(value).__name__
        message = f'unsupported metadata value type for {key!r}: {type_name}'
        raise InvalidResultError(message)
    return strings


def _string_tuple(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, (list, tuple)):
        return None
    strings = tuple(element for element in value if isinstance(element, str))
    return strings if len(strings) == len(value) else None
