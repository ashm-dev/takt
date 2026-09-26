"""Public library functions of takt: run, import and compare benchmarks.

The functions only assemble adapters, read the configuration and call the
use cases; the CLI and other front ends call these functions.
"""

import os
from collections.abc import Sequence
from pathlib import Path

from takt.application.multi_target.multi_target_writer import MultiTargetWriter
from takt.application.use_cases.compare_request import CompareRequest
from takt.application.use_cases.compare_suites import CompareSuites
from takt.application.use_cases.import_report import ImportReport
from takt.application.use_cases.import_request import ImportRequest
from takt.application.use_cases.import_suite import ImportSuite
from takt.application.use_cases.reject_single_strings import (
    reject_single_strings,
)
from takt.application.use_cases.run_request import RunRequest
from takt.application.use_cases.run_suite import RunSuite
from takt.domain.compare.compare_table import CompareTable
from takt.domain.errors.no_targets_error import NoTargetsError
from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.target import Target
from takt.domain.naming.name_template import NameTemplate
from takt.infrastructure.cache.file_schema_version_cache import (
    FileSchemaVersionCache,
)
from takt.infrastructure.clock.system_clock import SystemClock
from takt.infrastructure.config.config_sources import ConfigSources
from takt.infrastructure.config.resolve_name_template import (
    resolve_name_template,
)
from takt.infrastructure.config.resolve_targets import resolve_targets
from takt.infrastructure.db.alembic_schema_migrator import (
    AlembicSchemaMigrator,
)
from takt.infrastructure.db.sqlalchemy_target_connector import (
    SqlAlchemyTargetConnector,
)
from takt.infrastructure.pyperf.pyperf_result_reader import PyperfResultReader
from takt.infrastructure.runner.subprocess_benchmark_runner import (
    SubprocessBenchmarkRunner,
)


def run(
    runner_arguments: Sequence[str],
    *,
    db: Sequence[str] = (),
    target: Sequence[str] = (),
    config: Path | None = None,
    name: str | None = None,
) -> ImportReport:
    """Run benchmarks and write the result to every selected database.

    Targets and the run name template are checked before any benchmark
    starts; the length of the final name and a ``:`` that comes from the
    result are checked only after the benchmarks, and that error keeps the
    result file in its ``result_path`` attribute.
    A failed write does not raise: ``report.write.succeeded`` is ``False``
    and the result file stays on disk.

    :param runner_arguments: Arguments of ``pyperformance run``, or a pyperf
        script path followed by its arguments.
    :param db: SQLAlchemy URLs of target databases, like ``--db``.
    :param target: Target names from ``takt.toml``, like ``--target``.
    :param config: Path to ``takt.toml`` instead of ``./takt.toml``.
    :param name: Run name or name template, like ``--name``.
    :returns: The import report of the produced result file.
    :raises UsageError: If the configuration, targets or run name are
        invalid, ``-o``/``--output`` has no value, or a string is passed
        instead of a sequence of strings.
    :raises ExecutionError: If the benchmarks fail or the result file
        cannot be read.
    """
    reject_single_strings(
        runner_arguments=runner_arguments, db=db, target=target
    )
    targets, template = _configured(db, target, config, name)
    runner = SubprocessBenchmarkRunner(clock=SystemClock(), cwd=Path.cwd())
    return RunSuite(runner=runner, importer=_importer()).execute(
        RunRequest(
            runner_arguments=tuple(runner_arguments),
            targets=targets,
            name_template=template,
        ),
    )


def import_results(
    path: Path,
    *,
    db: Sequence[str] = (),
    target: Sequence[str] = (),
    config: Path | None = None,
    name: str | None = None,
) -> ImportReport:
    """Write a ready pyperf or pyperformance result to every database.

    A failed write does not raise: ``report.write.succeeded`` is ``False``.

    :param path: Result file, ``.json`` or ``.json.gz``.
    :param db: SQLAlchemy URLs of target databases, like ``--db``.
    :param target: Target names from ``takt.toml``, like ``--target``.
    :param config: Path to ``takt.toml`` instead of ``./takt.toml``.
    :param name: Run name or name template, like ``--name``.
    :returns: The import report of the result file.
    :raises UsageError: If the configuration, targets or run name are
        invalid, or a string is passed instead of a sequence of strings.
    :raises ExecutionError: If the result file cannot be read.
    """
    reject_single_strings(db=db, target=target)
    targets, template = _configured(db, target, config, name)
    return _importer().execute(
        ImportRequest(
            path=path,
            targets=targets,
            name_template=template,
            source=SuiteSource.IMPORT,
        ),
    )


def compare(
    operands: Sequence[str],
    *,
    db: Sequence[str] = (),
    target: Sequence[str] = (),
    config: Path | None = None,
) -> CompareTable:
    """Compare two or more results against the first one.

    Stored runs are read from the first configured target; operands that
    are all files need no database.

    :param operands: Result files, run names, ``name:N``, ``name:prefix``
        or hash prefixes; the first one is the base.
    :param db: SQLAlchemy URLs of target databases, like ``--db``.
    :param target: Target names from ``takt.toml``, like ``--target``.
    :param config: Path to ``takt.toml`` instead of ``./takt.toml``.
    :returns: The compare table.
    :raises UsageError: If the configuration is invalid, fewer than two
        operands are given, a stored run is requested without a target,
        or a string is passed instead of a sequence of strings.
    :raises ExecutionError: If an operand is not found or ambiguous, a
        result file cannot be read, the database cannot be connected to
        or read, or the suites share no benchmark.
    """
    reject_single_strings(operands=operands, db=db, target=target)
    targets = resolve_targets(_sources(db, target, config, None))
    selected = targets[0] if targets else None
    return CompareSuites(
        reader=PyperfResultReader(),
        connector=SqlAlchemyTargetConnector(),
    ).execute(CompareRequest(operands=tuple(operands), target=selected))


def _configured(
    db: Sequence[str],
    target: Sequence[str],
    config: Path | None,
    name: str | None,
) -> tuple[tuple[Target, ...], NameTemplate | None]:
    sources = _sources(db, target, config, name)
    targets = resolve_targets(sources)
    template = resolve_name_template(sources)
    if not targets:
        raise NoTargetsError
    return targets, template


def _sources(
    db: Sequence[str],
    target: Sequence[str],
    config: Path | None,
    name: str | None,
) -> ConfigSources:
    return ConfigSources(
        db_flags=tuple(db),
        target_flags=tuple(target),
        config_path=config,
        name_flag=name,
        environ=os.environ,
        cwd=Path.cwd(),
    )


def _writer() -> MultiTargetWriter:
    return MultiTargetWriter(
        connector=SqlAlchemyTargetConnector(),
        migrator=AlembicSchemaMigrator(),
        cache=FileSchemaVersionCache.default(os.environ),
    )


def _importer() -> ImportSuite:
    return ImportSuite(
        reader=PyperfResultReader(),
        writer=_writer(),
        clock=SystemClock(),
    )
