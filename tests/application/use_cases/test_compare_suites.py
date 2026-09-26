from pathlib import Path

import pytest

from takt.application.use_cases.compare_request import CompareRequest
from takt.application.use_cases.compare_suites import CompareSuites
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.model.target import Target
from tests.application.use_cases.compare_fakes import (
    HASH_A,
    HASH_B,
    HASH_C,
    FakeConnector,
    FakeReader,
    FakeSession,
    record,
    suite,
)
from tests.domain.exact_pattern import exact_pattern

TARGET = Target(name='main', url='sqlite:///main.db', dialect='sqlite')


class Fixture:
    def __init__(self, tmp_path: Path) -> None:
        self.base = tmp_path / 'base.json'
        self.new = tmp_path / 'new.json'
        self.base.write_text('{}')
        self.new.write_text('{}')
        self.session = FakeSession(
            (record(HASH_C, 'default'), record(HASH_B, None)),
        )
        self.connector = FakeConnector(self.session)
        self.use_case = CompareSuites(
            reader=FakeReader(
                {self.base: suite(HASH_A), self.new: suite(HASH_B)},
            ),
            connector=self.connector,
        )

    def execute(
        self,
        *operands: str,
        target: Target | None = TARGET,
    ) -> tuple[str, ...]:
        request = CompareRequest(operands=operands, target=target)
        return self.use_case.execute(request).headers


@pytest.fixture
def fixture(tmp_path: Path) -> Fixture:
    return Fixture(tmp_path)


def test_less_than_two_operands(fixture: Fixture) -> None:
    with pytest.raises(ConfigurationError) as excinfo:
        fixture.execute('a.json')

    assert str(excinfo.value) == 'compare needs at least two operands'
    assert fixture.connector.opened == []


def test_files_only_without_target(fixture: Fixture) -> None:
    files = (str(fixture.base), str(fixture.new))

    headers = fixture.execute(*files, target=None)

    assert headers == ('Benchmark', *files)
    assert fixture.connector.opened == []


def test_db_operand_without_target(fixture: Fixture) -> None:
    with pytest.raises(ConfigurationError) as excinfo:
        fixture.execute(str(fixture.base), 'default', target=None)

    assert str(excinfo.value) == (
        "operand 'default' is not a file and no database target is configured"
    )
    assert fixture.connector.opened == []


def test_mixed_operands(fixture: Fixture) -> None:
    headers = fixture.execute(str(fixture.base), 'default', '9c01de')

    assert headers == ('Benchmark', str(fixture.base), 'default', '9c01de')
    assert fixture.connector.opened == [TARGET]


def test_session_rolled_back_and_closed(fixture: Fixture) -> None:
    fixture.execute('default', str(fixture.new))

    assert fixture.session.calls == ['rollback', 'close']


def test_session_closed_on_error(fixture: Fixture) -> None:
    with pytest.raises(OperandNotFoundError):
        fixture.execute(str(fixture.base), 'nightly')

    assert fixture.session.calls == ['rollback', 'close']


def test_session_closed_when_rollback_fails(fixture: Fixture) -> None:
    fixture.session.rollback_error = RuntimeError('rollback failed')

    with pytest.raises(RuntimeError, match=exact_pattern('rollback failed')):
        fixture.execute('default', str(fixture.new))

    assert fixture.session.calls == ['rollback', 'close']
