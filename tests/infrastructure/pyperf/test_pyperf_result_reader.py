import gzip
import json
import math
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest

from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.domain.hashing.result_hash import result_hash
from takt.domain.model.benchmark import Benchmark
from takt.domain.model.suite import Suite
from takt.infrastructure.pyperf.pyperf_result_reader import PyperfResultReader

FIXTURES = Path(__file__).parent / 'fixtures'
FULL = FIXTURES / 'full.json'
OLD5 = FIXTURES / 'old5.json'


def _as_dict(node: object) -> dict[str, object]:
    assert isinstance(node, dict)
    return node


def _as_list(node: object) -> list[object]:
    assert isinstance(node, list)
    return node


def _full_document() -> dict[str, object]:
    return _as_dict(json.loads(FULL.read_text(encoding='utf-8')))


def _benchmark_metadata(
    document: dict[str, object], index: int
) -> dict[str, object]:
    benchmark = _as_dict(_as_list(document['benchmarks'])[index])
    return _as_dict(benchmark['metadata'])


def _all_metadata(document: dict[str, object]) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    for node in _as_list(document['benchmarks']):
        benchmark = _as_dict(node)
        found.append(_as_dict(benchmark['metadata']))
        for run_node in _as_list(benchmark['runs']):
            run_metadata = _as_dict(run_node).get('metadata')
            if run_metadata is not None:
                found.append(_as_dict(run_metadata))
    return found


def _write(tmp_path: Path, document: object) -> Path:
    path = tmp_path / 'result.json'
    path.write_text(json.dumps(document), encoding='utf-8')
    return path


def _read(path: Path) -> Suite:
    return PyperfResultReader().read(path)


def _check_nbody(nbody: Benchmark) -> None:
    calibration, measured = nbody.runs
    assert calibration.values == ()
    assert tuple(
        (warmup.loops, warmup.value) for warmup in calibration.warmups
    ) == ((1, 0.25), (2, 0.26), (4, 0.24))
    assert calibration.metadata.calibrate_loops == 4
    assert tuple(value.value for value in measured.values) == (0.21, 0.22, 0.2)
    assert measured.metadata.custom == {'my_label': 'baseline'}


def _check_json_dumps(json_dumps: Benchmark) -> None:
    assert len(json_dumps.runs) == 1
    metadata = json_dumps.runs[0].metadata
    assert metadata.tags == ('serialize',)
    assert metadata.python_hash_seed == '0'
    assert metadata.custom == {'duration': 2}
    assert metadata.hostname == 'bench-host'


def test_reads_full_fixture() -> None:
    suite = _read(FULL)

    assert suite.format_version == '1.0'
    assert suite.hash == result_hash(_full_document())
    assert tuple(bench.name for bench in suite.benchmarks) == (
        'nbody',
        'json_dumps',
    )
    nbody, json_dumps = suite.benchmarks
    _check_nbody(nbody)
    _check_json_dumps(json_dumps)
    assert suite.result_date == datetime.fromisoformat('2026-09-25 09:59:00')


def test_gzip_has_same_hash(tmp_path: Path) -> None:
    compressed = tmp_path / 'full.json.gz'
    with gzip.open(compressed, 'wt', encoding='utf-8') as gzip_file:
        gzip_file.write(FULL.read_text(encoding='utf-8'))

    assert _read(compressed).hash == _read(FULL).hash


def test_reformatted_json_has_same_hash(tmp_path: Path) -> None:
    reformatted = tmp_path / 'full.json'
    reformatted.write_text(
        json.dumps(_full_document(), indent=4), encoding='utf-8'
    )

    assert _read(reformatted).hash == _read(FULL).hash


def test_reads_old_format5() -> None:
    suite = _read(OLD5)

    assert suite.format_version == '5'
    assert tuple(bench.name for bench in suite.benchmarks) == ('telco',)
    runs = suite.benchmarks[0].runs
    assert len(runs) == 1
    run = runs[0]
    values = tuple(measurement.value for measurement in run.values)
    assert values == (0.05, 0.06)
    assert tuple(warmup.loops for warmup in run.warmups) == (2,)
    assert run.warmups[0].value == pytest.approx(0.1)
    assert run.metadata.hostname == 'old-host'
    assert run.metadata.inner_loops == 2


def test_unsupported_version_raises(tmp_path: Path) -> None:
    document = _full_document()
    document['version'] = '2.0'
    path = _write(tmp_path, document)

    with pytest.raises(InvalidResultError) as error:
        _read(path)

    assert str(error.value) == (
        f"invalid pyperf result {path}: unsupported format version '2.0'"
    )


def test_missing_version_raises(tmp_path: Path) -> None:
    path = _write(tmp_path, {'benchmarks': []})

    with pytest.raises(InvalidResultError) as error:
        _read(path)

    assert str(error.value).endswith("missing 'version'")


def test_pyperf_rejects_file(tmp_path: Path) -> None:
    path = _write(tmp_path, {'version': '1.0', 'benchmarks': []})

    with pytest.raises(InvalidResultError) as error:
        _read(path)

    assert str(error.value).startswith('invalid pyperf result ')


def test_result_date_none_without_dates(tmp_path: Path) -> None:
    document = _full_document()
    for metadata in _all_metadata(document):
        metadata.pop('date', None)

    assert _read(_write(tmp_path, document)).result_date is None


def test_bad_date_is_skipped(tmp_path: Path) -> None:
    document = _full_document()
    _benchmark_metadata(document, 1)['date'] = 'yesterday'

    suite = _read(_write(tmp_path, document))

    assert suite.result_date == datetime.fromisoformat(
        '2026-09-25 10:00:00.000001'
    )


@pytest.mark.parametrize(
    'value',
    [math.nan, math.inf, '\ud800'],
    ids=['nan', 'infinity', 'lone-surrogate'],
)
def test_unhashable_document_raises(tmp_path: Path, value: object) -> None:
    document = _full_document()
    _benchmark_metadata(document, 0)['extra'] = value
    path = _write(tmp_path, document)

    with pytest.raises(InvalidResultError) as error:
        _read(path)

    assert str(error.value).startswith(f'invalid pyperf result {path}: ')
    assert isinstance(error.value.__cause__, ValueError)


@pytest.mark.usefixtures('local_time_plus_three_hours')
def test_aware_date_mixes_with_naive_dates(tmp_path: Path) -> None:
    document = _full_document()
    _benchmark_metadata(document, 1)['date'] = '2026-09-25 06:30:00+00:00'

    suite = _read(_write(tmp_path, document))

    assert suite.result_date == datetime.fromisoformat('2026-09-25 09:30:00')


@pytest.mark.usefixtures('local_time_plus_three_hours')
def test_all_aware_dates_give_naive_date(tmp_path: Path) -> None:
    document = _full_document()
    for metadata in _all_metadata(document):
        date = metadata.get('date')
        if date is not None:
            metadata['date'] = f'{date}+00:00'

    suite = _read(_write(tmp_path, document))

    assert suite.result_date == datetime.fromisoformat('2026-09-25 12:59:00')


@pytest.mark.parametrize(('name', 'type_name'), [(123, 'int'), (1.5, 'float')])
def test_non_string_benchmark_name_raises(
    tmp_path: Path, name: object, type_name: str
) -> None:
    document = _full_document()
    _benchmark_metadata(document, 1)['name'] = name
    path = _write(tmp_path, document)

    with pytest.raises(InvalidResultError) as error:
        _read(path)

    assert str(error.value) == (
        f'invalid pyperf result {path}: '
        f'benchmark name must be a string, got {type_name}'
    )


def _bad_hash(_document: object) -> str:
    return 'bad'


def _overflow_stack(_document: object) -> str:
    # A real input hits this only in a stack-dependent depth window.
    msg = 'maximum recursion depth exceeded'
    raise RecursionError(msg)


@pytest.mark.parametrize(
    ('fake_hash', 'message', 'cause'),
    [
        (
            _bad_hash,
            'suite hash must be 64 lowercase hex characters',
            ValueError,
        ),
        (_overflow_stack, 'maximum recursion depth exceeded', RecursionError),
    ],
    ids=['domain-invariant', 'too-deep-document'],
)
def test_suite_build_error_raises(
    monkeypatch: pytest.MonkeyPatch,
    fake_hash: Callable[[object], str],
    message: str,
    cause: type[Exception],
) -> None:
    monkeypatch.setattr(
        'takt.infrastructure.pyperf.pyperf_result_reader.result_hash',
        fake_hash,
    )

    with pytest.raises(InvalidResultError) as error:
        _read(FULL)

    assert str(error.value) == f'invalid pyperf result {FULL}: {message}'
    assert isinstance(error.value.__cause__, cause)


@pytest.mark.parametrize(
    ('run_index', 'key', 'numbers'),
    [
        (1, 'values', [10**400]),
        (0, 'warmups', [[4, 10**400]]),
    ],
    ids=['value', 'warmup'],
)
def test_number_too_large_for_float_raises(
    tmp_path: Path, run_index: int, key: str, numbers: list[object]
) -> None:
    broken = _full_document()
    benchmark = _as_dict(_as_list(broken['benchmarks'])[0])
    _as_dict(_as_list(benchmark['runs'])[run_index])[key] = numbers
    path = _write(tmp_path, broken)

    with pytest.raises(InvalidResultError) as error:
        _read(path)

    assert str(error.value) == (
        f'invalid pyperf result {path}: int too large to convert to float'
    )
    assert isinstance(error.value.__cause__, OverflowError)
