from takt.domain.model.metadata_key_types import METADATA_KEY_TYPES
from takt.domain.model.run_metadata import RunMetadata


def test_run_metadata_defaults_are_empty() -> None:
    metadata = RunMetadata()

    assert all(getattr(metadata, key) is None for key in METADATA_KEY_TYPES)
    assert metadata.custom == {}
