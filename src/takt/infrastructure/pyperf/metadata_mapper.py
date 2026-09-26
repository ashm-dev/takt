"""Mapping of raw pyperf metadata to ``RunMetadata``."""

import copy
from collections.abc import Mapping

from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.domain.model.metadata_key_types import METADATA_KEY_TYPES
from takt.domain.model.metadata_value import MetadataValue
from takt.domain.model.run_metadata import RunMetadata


def to_run_metadata(metadata: Mapping[str, object]) -> RunMetadata:
    """Split raw metadata into known fields and custom keys.

    A known key goes to its field when its value has exactly the field type
    or converts to it; otherwise it goes to ``custom`` with the unknown keys.
    An ``int`` ``python_hash_seed`` converts to a ``str``, and a ``list`` of
    strings converts to a ``tuple`` both in ``tags`` and in ``custom``.

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
    field_type = METADATA_KEY_TYPES.get(key)
    if field_type is tuple:
        return _string_tuple(value)
    if isinstance(value, bool):
        return None
    if key == 'python_hash_seed' and isinstance(value, int):
        return str(value)
    if field_type is not None and isinstance(value, field_type):
        return value
    return None


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
