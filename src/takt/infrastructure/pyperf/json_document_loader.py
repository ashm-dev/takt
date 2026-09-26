"""Loading of a pyperf JSON or JSON.gz file as a parsed document."""

import gzip
import json
import zlib
from pathlib import Path
from typing import Final, TextIO

from takt.domain.errors.invalid_result_error import InvalidResultError

# ValueError also covers bad UTF-8, bad JSON and integers over the digit limit.
_READ_ERRORS: Final = (
    OSError,
    EOFError,
    ValueError,
    RecursionError,
    zlib.error,
)


def load_json_document(path: Path) -> object:
    """Read a JSON or gzip-compressed JSON file.

    :param path: Path to a ``*.json`` or ``*.json.gz`` file.
    :returns: The parsed JSON document as is.
    :raises InvalidResultError: If the file cannot be opened, decompressed,
        decoded or parsed.
    """
    try:
        with _open_text(path) as text_file:
            return json.load(text_file)
    except _READ_ERRORS as exc:
        message = f'cannot read pyperf result {path}: {exc}'
        raise InvalidResultError(message) from exc


def _open_text(path: Path) -> TextIO:
    if path.name.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8')
    return path.open('r', encoding='utf-8')
