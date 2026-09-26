"""Reader of pyperf and pyperformance result files."""

from pathlib import Path
from typing import Final

import pyperf

from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.domain.hashing.result_hash import result_hash
from takt.domain.model.benchmark import Benchmark
from takt.domain.model.measurement import Measurement
from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.suite import Suite
from takt.domain.model.worker_run import WorkerRun
from takt.infrastructure.pyperf import (
    json_document_loader,
    metadata_flattener,
    metadata_mapper,
    run_date_parser,
)

_FORMAT_VERSIONS: Final[frozenset[str]] = frozenset(('1.0', '5', '6'))


class PyperfResultReader:
    """Reader of pyperf and pyperformance JSON or JSON.gz results."""

    def read(self, path: Path) -> Suite:
        """Read a pyperf result file into a suite.

        The hash comes from the decompressed JSON document, and the
        structure comes from the public pyperf API.

        :param path: Path to a ``*.json`` or ``*.json.gz`` result.
        :returns: The suite from the file.
        :raises InvalidResultError: If the file cannot be read, has an
            unsupported format or breaks a domain invariant.
        """
        document = json_document_loader.load_json_document(path)
        format_version = _format_version(document, path)
        pyperf_suite = _load_pyperf_suite(path)
        try:
            return _suite(result_hash(document), format_version, pyperf_suite)
        except ValueError as exc:
            message = f'invalid pyperf result {path}: {exc}'
            raise InvalidResultError(message) from exc


def _format_version(document: object, path: Path) -> str:
    if not isinstance(document, dict) or 'version' not in document:
        message = f"invalid pyperf result {path}: missing 'version'"
        raise InvalidResultError(message)
    format_version = str(document['version'])
    if format_version not in _FORMAT_VERSIONS:
        message = (
            f'invalid pyperf result {path}: '
            f'unsupported format version {format_version!r}'
        )
        raise InvalidResultError(message)
    return format_version


def _load_pyperf_suite(path: Path) -> pyperf.BenchmarkSuite:
    try:
        return pyperf.BenchmarkSuite.load(str(path))
    except Exception as exc:
        message = f'invalid pyperf result {path}: {exc}'
        raise InvalidResultError(message) from exc


def _suite(
    suite_hash: str,
    format_version: str,
    pyperf_suite: pyperf.BenchmarkSuite,
) -> Suite:
    benchmarks = tuple(
        _benchmark(bench) for bench in pyperf_suite.get_benchmarks()
    )
    dates = tuple(
        run_date_parser.parse_run_date(worker_run.metadata.date)
        for benchmark in benchmarks
        for worker_run in benchmark.runs
    )
    return Suite(
        hash=suite_hash,
        format_version=format_version,
        result_date=min(
            (date for date in dates if date is not None),
            default=None,
        ),
        benchmarks=benchmarks,
    )


def _benchmark(bench: pyperf.Benchmark) -> Benchmark:
    return Benchmark(
        name=bench.get_name(),
        runs=tuple(_worker_run(run) for run in bench.get_runs()),
    )


def _worker_run(run: pyperf.Run) -> WorkerRun:
    metadata = metadata_flattener.flatten_metadata(run)
    return WorkerRun(
        metadata=metadata_mapper.to_run_metadata(metadata),
        warmups=tuple(
            Measurement(
                kind=MeasurementKind.WARMUP,
                loops=loops,
                value=float(warmup_value),
            )
            for loops, warmup_value in run.warmups
        ),
        values=tuple(
            Measurement(
                kind=MeasurementKind.VALUE,
                loops=None,
                value=float(run_value),
            )
            for run_value in run.values
        ),
    )
