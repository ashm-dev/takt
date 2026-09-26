from datetime import UTC, datetime
from pathlib import Path

import pytest

from takt.application.multi_target.multi_target_writer import MultiTargetWriter
from takt.application.use_cases.import_suite import ImportSuite
from takt.application.use_cases.run_request import RunRequest
from takt.application.use_cases.run_suite import RunSuite
from takt.domain.errors.benchmark_failed_error import BenchmarkFailedError
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.target import Target
from takt.domain.naming.name_template import NameTemplate
from tests.application.multi_target.fakes import (
    FakeCache,
    FakeConnector,
    FakeMigrator,
    FakeWorld,
)
from tests.application.use_cases.fakes import (
    FakeReader,
    FakeRunner,
    FixedClock,
    make_suite,
)

TARGET = Target(name='a', url='sqlite:///a.db', dialect='sqlite')
NOW = datetime(2026, 9, 25, 13, 46, 1, tzinfo=UTC)
RESULT_PATH = Path('takt-20260925T134601Z.json')


class Fixture:
    def __init__(
        self,
        world: FakeWorld,
        result_path: Path | None = RESULT_PATH,
        runner_error: Exception | None = None,
        reader_error: Exception | None = None,
    ) -> None:
        self.runner = FakeRunner(result_path, error=runner_error)
        self.reader = FakeReader(make_suite(), error=reader_error)
        self.clock = FixedClock(NOW)
        importer = ImportSuite(
            reader=self.reader,
            writer=MultiTargetWriter(
                connector=FakeConnector(world),
                migrator=FakeMigrator(world),
                cache=FakeCache(world),
            ),
            clock=self.clock,
        )
        self.use_case = RunSuite(runner=self.runner, importer=importer)


def request(
    *,
    runner_arguments: tuple[str, ...] = (),
    targets: tuple[Target, ...] = (TARGET,),
    name_template: NameTemplate | None = None,
) -> RunRequest:
    return RunRequest(
        runner_arguments=runner_arguments,
        targets=targets,
        name_template=name_template,
    )


def test_empty_targets_do_not_start_benchmarks() -> None:
    world = FakeWorld()
    fixture = Fixture(world)

    with pytest.raises(ConfigurationError) as excinfo:
        fixture.use_case.execute(request(targets=()))

    assert str(excinfo.value) == (
        'no database targets configured: '
        'use --db, --target, TAKT_DB or takt.toml'
    )
    assert fixture.runner.calls == []


def test_runner_receives_arguments_unchanged() -> None:
    world = FakeWorld()
    fixture = Fixture(world)
    arguments = ('-b', 'nbody', '--fast')

    fixture.use_case.execute(request(runner_arguments=arguments))

    assert fixture.runner.calls == [arguments]


def test_result_is_imported_with_run_source() -> None:
    world = FakeWorld()
    fixture = Fixture(world)

    report = fixture.use_case.execute(request())

    assert fixture.reader.calls == [RESULT_PATH]
    assert world.inserted[-1].source == SuiteSource.RUN
    assert report.write.succeeded


def test_runner_failure_propagates_and_writes_nothing() -> None:
    world = FakeWorld()
    error = BenchmarkFailedError(
        'pyperformance exited with code 1',
        return_code=1,
    )
    fixture = Fixture(world, result_path=None, runner_error=error)

    with pytest.raises(BenchmarkFailedError):
        fixture.use_case.execute(request())

    assert fixture.reader.calls == []
    assert world.journal == []


def test_failed_write_returns_report_with_result_path() -> None:
    world = FakeWorld(fail={'insert:a': 1})
    fixture = Fixture(world)

    report = fixture.use_case.execute(request())

    assert report.write.succeeded is False
    assert report.result_path == RESULT_PATH


def test_name_template_is_passed_to_import() -> None:
    world = FakeWorld()
    template = NameTemplate.parse('{hash}')
    fixture = Fixture(world)

    report = fixture.use_case.execute(request(name_template=template))

    assert report.name == 'ffffffffffff'


def test_invalid_result_propagates() -> None:
    world = FakeWorld()
    fixture = Fixture(world, reader_error=InvalidResultError('bad json'))

    with pytest.raises(InvalidResultError):
        fixture.use_case.execute(request())

    assert len(fixture.runner.calls) == 1


def test_invalid_rendered_name_keeps_result_path() -> None:
    world = FakeWorld()
    fixture = Fixture(world)
    template = NameTemplate.parse('{hash}' * 22)

    with pytest.raises(InvalidRunNameError) as excinfo:
        fixture.use_case.execute(request(name_template=template))

    assert excinfo.value.result_path == RESULT_PATH
    assert world.journal == []
