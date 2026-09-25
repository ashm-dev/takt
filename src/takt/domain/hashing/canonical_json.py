"""Canonical JSON serialization."""

import json


def canonical_json(document: object) -> bytes:
    """Serialize a parsed JSON document in one fixed form.

    Keys are sorted, separators have no spaces, non-ASCII text stays as
    UTF-8, and NaN or infinity are rejected.

    :param document: Parsed JSON document.
    :returns: UTF-8 bytes of the canonical JSON.
    :raises TypeError: If the document has a value that JSON cannot hold.
    :raises ValueError: If the document has NaN or infinity.
    """
    text = json.dumps(
        document,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode()
