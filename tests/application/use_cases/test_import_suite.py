from datetime import UTC, datetime
from pathlib import Path

import pytest

from takt.application.multi_target.multi_target_writer import MultiTargetWriter
from takt.application.multi_target.target_status import TargetStatus
from takt.application.use_cases.import_request import ImportRequest
from takt.application.use_cases.import_suite import ImportSuite
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.errors.write_interrupted_error import WriteInterruptedError
from takt.domain.model.suite import Suite
from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.target import Target
from takt.domain.naming.name_template import NameTemplate
from takt.domain.naming.name_values import NameValues
from tests.application.multi_target.fakes import (
    FakeCache,
    FakeConnector,
    FakeMigrator,
    FakeSession,
    FakeWorld,
)
from tests.application.use_cases.fakes import FakeReader, FixedClock, make_suite

TARGET = Target(name='a', url='sqlite:///a.db', dialect='sqlite')
NOW = datetime(2026, 9, 25, 13, 46, 1, tzinfo=UTC)
RESULT_PATH = Path('results/run.json')


class Fixture:
    def __init__(
        self,
        world: FakeWorld,
        suite: Suite | None = None,
        error: Exception | None = None,
    ) -> None:
        self.suite = suite or make_suite()
        self.reader = FakeReader(self.suite, error=error)
        self.clock = FixedClock(NOW)
        self.use_case = ImportSuite(
            reader=self.reader,
            writer=MultiTargetWriter(
                connector=FakeConnector(world),
                migrator=FakeMigrator(world),
                cache=FakeCache(world),
            ),
            clock=self.clock,
        )


def request(
    *,
    targets: tuple[Target, ...] = (TARGET,),
    name_template: NameTemplate | None = None,
    source: SuiteSource = SuiteSource.IMPORT,
) -> ImportRequest:
    return ImportRequest(
        path=RESULT_PATH,
        targets=targets,
        name_template=name_template,
        source=source,
    )


def test_empty_targets_raise_configuration_error() -> None:
    world = FakeWorld()
    fixture = Fixture(world)

    with pytest.raises(ConfigurationError) as excinfo:
        fixture.use_case.execute(request(targets=()))

    assert str(excinfo.value) == (
        'no database targets configured: '
        'use --db, --target, TAKT_DB or takt.toml'
    )
    assert fixture.reader.calls == []


def test_import_without_template_writes_null_name() -> None:
    world = FakeWorld()
    fixture = Fixture(world)

    report = fixture.use_case.execute(request())

    assert report.name is None
    assert 'a' in world.stored
    assert report.write.succeeded
    assert report.suite_hash == 'f' * 64
    assert report.result_path == RESULT_PATH


def test_import_renders_name_from_template() -> None:
    world = FakeWorld()
    template = NameTemplate.parse('{python_version}-{hostname}-{hash}')
    fixture = Fixture(world)

    report = fixture.use_case.execute(request(name_template=template))

    assert report.name == '3.14.0-bench-host-ffffffffffff'
    assert world.inserted[-1].name == report.name


def test_clock_called_once_and_used_for_loaded_at() -> None:
    world = FakeWorld()
    template = NameTemplate.parse('{datetime}/{date}/{path}')
    fixture = Fixture(world)

    report = fixture.use_case.execute(request(name_template=template))

    assert fixture.clock.calls == 1
    assert world.inserted[-1].loaded_at == NOW
    assert report.name == '2026-09-25T13-46-01Z/2026-09-25/run'


def test_source_is_passed_to_record() -> None:
    world = FakeWorld()
    fixture = Fixture(world)

    fixture.use_case.execute(request(source=SuiteSource.RUN))

    assert world.inserted[-1].source == SuiteSource.RUN


def test_reader_error_propagates() -> None:
    world = FakeWorld()
    fixture = Fixture(world, error=InvalidResultError('bad json'))

    with pytest.raises(InvalidResultError):
        fixture.use_case.execute(request())

    assert world.journal == []


def test_invalid_rendered_name_propagates() -> None:
    world = FakeWorld()
    template = NameTemplate.parse('{hostname}')
    fixture = Fixture(world, suite=make_suite(hostname='a:b'))

    with pytest.raises(InvalidRunNameError):
        fixture.use_case.execute(request(name_template=template))

    assert world.journal == []


def _press_ctrl_c(_session: FakeSession) -> None:
    raise KeyboardInterrupt


def test_ctrl_c_during_write_names_result_and_run_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(FakeSession, 'commit', _press_ctrl_c)
    template = NameTemplate.parse('nightly {date}')
    fixture = Fixture(FakeWorld())

    with pytest.raises(KeyboardInterrupt) as caught:
        fixture.use_case.execute(request(name_template=template))

    assert isinstance(caught.value.__cause__, WriteInterruptedError)
    assert caught.value.__cause__.result_path == RESULT_PATH
    assert caught.value.__cause__.name == 'nightly 2026-09-25'


def test_already_loaded_keeps_old_name() -> None:
    world = FakeWorld(loaded={'a': 'old'})
    template = NameTemplate.parse('new')
    fixture = Fixture(world)

    report = fixture.use_case.execute(request(name_template=template))

    assert report.name == 'new'
    assert report.write.outcomes[0].status == TargetStatus.ALREADY_LOADED
    assert report.write.outcomes[0].existing_name == 'old'
    assert report.write.succeeded


def test_failed_write_is_returned_not_raised() -> None:
    world = FakeWorld(fail={'insert:a': 1})
    fixture = Fixture(world)

    report = fixture.use_case.execute(request())

    assert report.write.succeeded is False
    assert report.write.outcomes[0].status == TargetStatus.FAILED


def test_python_version_and_hostname_may_be_missing() -> None:
    world = FakeWorld()
    template = NameTemplate.parse('{python_version}')
    fixture = Fixture(
        world, suite=make_suite(python_version=None, hostname=None)
    )

    report = fixture.use_case.execute(request(name_template=template))

    expected = template.render(
        NameValues(
            now=NOW,
            result_path=RESULT_PATH,
            python_version=None,
            hostname=None,
            suite_hash=fixture.suite.hash,
        ),
    )
    assert report.name == expected
