import dataclasses

from takt.domain.model.known_metadata_keys import KNOWN_METADATA_KEYS
from takt.domain.model.run_metadata import RunMetadata


def test_run_metadata_defaults_are_empty() -> None:
    metadata = RunMetadata()

    assert all(getattr(metadata, key) is None for key in KNOWN_METADATA_KEYS)
    assert metadata.custom == {}


def test_known_metadata_keys_match_fields() -> None:
    field_names = tuple(
        field.name
        for field in dataclasses.fields(RunMetadata)
        if field.name != 'custom'
    )

    assert field_names == KNOWN_METADATA_KEYS
    assert len(KNOWN_METADATA_KEYS) == 49
