import hashlib
import json
import os
from pathlib import Path

import pytest

from takt.infrastructure.cache.file_schema_version_cache import (
    FileSchemaVersionCache,
)

URL_A = 'sqlite:///a.db'
URL_B = 'sqlite:///b.db'
REPLACE_ERROR = 'boom'
HOME_CACHE = Path.home() / '.cache' / 'takt' / 'schema_versions.json'


def url_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def fail_replace(*_args: object) -> None:
    raise OSError(REPLACE_ERROR)


@pytest.fixture
def cache(tmp_path: Path) -> FileSchemaVersionCache:
    return FileSchemaVersionCache(file_path=tmp_path / 'cache.json')


def test_default_uses_xdg_cache_home(tmp_path: Path) -> None:
    cache = FileSchemaVersionCache.default({'XDG_CACHE_HOME': str(tmp_path)})

    assert cache.file_path == tmp_path / 'takt' / 'schema_versions.json'


def test_default_falls_back_to_home_cache() -> None:
    assert FileSchemaVersionCache.default({}).file_path == HOME_CACHE


def test_default_ignores_relative_xdg_cache_home() -> None:
    cache = FileSchemaVersionCache.default({'XDG_CACHE_HOME': 'relative/dir'})

    assert cache.file_path == HOME_CACHE


def test_get_returns_none_when_file_missing(
    cache: FileSchemaVersionCache,
) -> None:
    assert cache.get(URL_A) is None
    assert not cache.file_path.exists()


def test_put_then_get_returns_revision(cache: FileSchemaVersionCache) -> None:
    cache.put(URL_A, '0001')

    assert cache.get(URL_A) == '0001'
    assert cache.get(URL_B) is None


def test_put_creates_parent_directories(tmp_path: Path) -> None:
    cache = FileSchemaVersionCache(
        file_path=tmp_path / 'x' / 'y' / 'cache.json',
    )

    cache.put(URL_A, '0001')

    assert cache.file_path.exists()


def test_file_does_not_contain_url(cache: FileSchemaVersionCache) -> None:
    url = 'mariadb+pymysql://user:secret@h/db'

    cache.put(url, '0001')

    text = cache.file_path.read_text(encoding='utf-8')
    assert 'secret' not in text
    assert 'mariadb' not in text
    assert url_key(url) in text


def test_forget_removes_only_given_url(cache: FileSchemaVersionCache) -> None:
    cache.put(URL_A, '0001')
    cache.put(URL_B, '0001')

    cache.forget(URL_A)

    assert cache.get(URL_A) is None
    assert cache.get(URL_B) == '0001'


def test_forget_missing_url_does_not_create_file(
    cache: FileSchemaVersionCache,
) -> None:
    cache.forget(URL_A)

    assert not cache.file_path.exists()


def test_corrupted_file_is_treated_as_empty(
    cache: FileSchemaVersionCache,
) -> None:
    cache.file_path.write_text('{not json', encoding='utf-8')

    assert cache.get(URL_A) is None

    cache.put(URL_A, '0001')

    document = json.loads(cache.file_path.read_text(encoding='utf-8'))
    assert document == {url_key(URL_A): '0001'}


def test_non_object_root_is_treated_as_empty(
    cache: FileSchemaVersionCache,
) -> None:
    cache.file_path.write_text('[1, 2]', encoding='utf-8')

    assert cache.get(URL_A) is None


def test_non_string_entries_are_ignored(cache: FileSchemaVersionCache) -> None:
    cache.file_path.write_text(
        json.dumps({url_key(URL_A): 5, url_key(URL_B): '0001'}),
        encoding='utf-8',
    )

    assert cache.get(URL_A) is None
    assert cache.get(URL_B) == '0001'


def test_put_leaves_no_temp_files(
    tmp_path: Path,
    cache: FileSchemaVersionCache,
) -> None:
    cache.put(URL_A, '0001')
    cache.put(URL_B, '0001')

    assert [path.name for path in tmp_path.iterdir()] == ['cache.json']


def test_put_removes_temp_file_on_replace_error(
    tmp_path: Path,
    cache: FileSchemaVersionCache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, 'replace', fail_replace)
    with pytest.raises(OSError, match=REPLACE_ERROR):
        cache.put(URL_A, '0001')

    assert list(tmp_path.glob('*.tmp')) == []
