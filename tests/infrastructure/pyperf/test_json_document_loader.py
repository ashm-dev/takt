import gzip
from pathlib import Path

import pytest

from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.infrastructure.pyperf.json_document_loader import load_json_document

FULL = Path(__file__).parent / 'fixtures' / 'full.json'


def test_reads_plain_json() -> None:
    document = load_json_document(FULL)

    assert isinstance(document, dict)
    assert document['version'] == '1.0'


def test_reads_gzip_json(tmp_path: Path) -> None:
    compressed = tmp_path / 'full.json.gz'
    with gzip.open(compressed, 'wt', encoding='utf-8') as gzip_file:
        gzip_file.write(FULL.read_text(encoding='utf-8'))

    assert load_json_document(compressed) == load_json_document(FULL)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(InvalidResultError) as error:
        load_json_document(tmp_path / 'nope.json')

    assert str(error.value).startswith('cannot read pyperf result ')


def test_broken_json_raises(tmp_path: Path) -> None:
    broken = tmp_path / 'broken.json'
    broken.write_text('{"version": ', encoding='utf-8')

    with pytest.raises(InvalidResultError) as error:
        load_json_document(broken)

    assert str(error.value).startswith('cannot read pyperf result ')


def test_broken_gzip_raises(tmp_path: Path) -> None:
    broken = tmp_path / 'bad.json.gz'
    broken.write_bytes(b'not gzip')

    with pytest.raises(InvalidResultError):
        load_json_document(broken)
