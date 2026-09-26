import dataclasses
import typing

from takt.domain.model.metadata_key_types import METADATA_KEY_TYPES
from takt.domain.model.run_metadata import RunMetadata


def _field_type(annotation: object) -> object:
    field_annotation = typing.get_args(annotation)[0]
    return typing.get_origin(field_annotation) or field_annotation


def test_key_types_match_run_metadata_fields() -> None:
    hints = typing.get_type_hints(RunMetadata)
    field_types = tuple(
        (field.name, _field_type(hints[field.name]))
        for field in dataclasses.fields(RunMetadata)
        if field.name != 'custom'
    )

    assert field_types == tuple(METADATA_KEY_TYPES.items())
    assert len(METADATA_KEY_TYPES) == 49
