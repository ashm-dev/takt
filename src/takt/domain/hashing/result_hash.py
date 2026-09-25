"""Hash of a pyperf result."""

import hashlib

from takt.domain.hashing.canonical_json import canonical_json


def result_hash(document: object) -> str:
    """Return the SHA-256 of the canonical JSON of a parsed result.

    :param document: Parsed JSON document of a pyperf result.
    :returns: 64 lowercase hex characters.
    :raises TypeError: If the document has a value that JSON cannot hold.
    :raises ValueError: If the document has NaN or infinity.
    """
    return hashlib.sha256(canonical_json(document)).hexdigest()
