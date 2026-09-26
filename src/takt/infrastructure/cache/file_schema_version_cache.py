"""Schema version cache stored in a local JSON file."""

import contextlib
import hashlib
import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import IO


class FileSchemaVersionCache:
    """Remember the schema revision already applied to each target URL.

    The cache only lets takt skip schema checks, so a file that cannot be
    read counts as empty and a failed write is skipped.
    """

    def __init__(self, *, file_path: Path) -> None:
        """Create a cache backed by a file.

        :param file_path: JSON file; it is created on the first write.
        """
        self.file_path = file_path

    @classmethod
    def default(cls, environ: Mapping[str, str]) -> FileSchemaVersionCache:
        """Create the cache in the user cache directory.

        :param environ: Environment variables.
        :returns: Cache under ``$XDG_CACHE_HOME/takt`` or ``~/.cache/takt``.
        """
        cache_home = environ.get('XDG_CACHE_HOME', '')
        if cache_home and Path(cache_home).is_absolute():
            base = Path(cache_home)
        else:
            base = Path.home() / '.cache'
        return cls(file_path=base / 'takt' / 'schema_versions.json')

    def get(self, url: str) -> str | None:
        """Return the revision remembered for a URL.

        :param url: Target URL.
        :returns: Revision or ``None`` when nothing is remembered.
        """
        return _read_entries(self.file_path).get(_url_key(url))

    def put(self, url: str, revision: str) -> None:
        """Remember the revision applied to a URL.

        :param url: Target URL.
        :param revision: Applied schema revision.
        """
        entries = _read_entries(self.file_path)
        entries[_url_key(url)] = revision
        with contextlib.suppress(OSError):
            _write_entries(self.file_path, entries)

    def forget(self, url: str) -> None:
        """Drop the revision remembered for a URL.

        :param url: Target URL.
        """
        entries = _read_entries(self.file_path)
        if entries.pop(_url_key(url), None) is not None:
            with contextlib.suppress(OSError):
                _write_entries(self.file_path, entries)


def _url_key(url: str) -> str:
    # The URL may contain a password, so only its digest is stored.
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def _read_entries(file_path: Path) -> dict[str, str]:
    try:
        document: object = json.loads(file_path.read_text(encoding='utf-8'))
    except OSError, json.JSONDecodeError, UnicodeDecodeError:
        return {}
    if not isinstance(document, dict):
        return {}
    return {
        key: value
        for key, value in document.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def _write_entries(file_path: Path, entries: dict[str, str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        'w',
        encoding='utf-8',
        dir=file_path.parent,
        delete=False,
        suffix='.tmp',
    ) as stream:
        temporary_path = Path(stream.name)
        try:
            _replace_with_stream(stream, entries, file_path)
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise


def _replace_with_stream(
    stream: IO[str],
    entries: dict[str, str],
    file_path: Path,
) -> None:
    json.dump(entries, stream, sort_keys=True)
    stream.close()
    Path(stream.name).replace(file_path)
