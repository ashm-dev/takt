from datetime import datetime
from pathlib import Path

import pytest

from takt.application.use_cases.operand_resolver import OperandResolver
from takt.domain.compare.labeled_suite import LabeledSuite
from takt.domain.errors.ambiguous_operand_error import AmbiguousOperandError
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.errors.takt_error import TaktError
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.operand.file_operand import FileOperand
from takt.domain.operand.operand import Operand
from takt.domain.operand.plain_operand import PlainOperand
from takt.domain.operand.tagged_operand import TaggedOperand
from tests.application.use_cases.compare_fakes import (
    HASH_A,
    HASH_B,
    HASH_C,
    FakeReader,
    FakeSession,
    record,
    suite,
)

FIRST_DATE = datetime.fromisoformat('2026-09-01 10:00')
SECOND_DATE = datetime.fromisoformat('2026-09-02 10:00')
DEFAULT_RUNS = (
    record(HASH_C, 'default'),
    record(HASH_B, 'default', SECOND_DATE),
    record(HASH_A, 'default', FIRST_DATE),
)


def resolve(session: FakeSession | None, operand: Operand) -> LabeledSuite:
    return OperandResolver(reader=FakeReader({}), session=session).resolve(
        operand,
    )


def failure(
    session: FakeSession | None,
    operand: Operand,
    error_type: type[TaktError],
) -> str:
    try:
        resolve(session, operand)
    except error_type as error:
        return str(error)
    pytest.fail('operand was resolved')


def tagged(
    text: str,
    *,
    index: int | None = None,
    hash_prefix: str | None = None,
) -> TaggedOperand:
    return TaggedOperand(
        text=text,
        name='default',
        index=index,
        hash_prefix=hash_prefix,
    )


def session_with(*records: SuiteRecord) -> FakeSession:
    return FakeSession(records)


def test_file_operand() -> None:
    path = Path('/home/u/r.json')
    expected = suite(HASH_A)
    file_resolver = OperandResolver(
        reader=FakeReader({path: expected}),
        session=None,
    )

    labeled = file_resolver.resolve(FileOperand(text='~/r.json', path=path))

    assert labeled.label == '~/r.json'
    assert labeled.suite == expected


def test_db_operand_without_session() -> None:
    message = failure(None, PlainOperand(text='default'), ConfigurationError)

    assert message == (
        "operand 'default' is not a file and no database target is configured"
    )


def test_plain_unique_name() -> None:
    session = session_with(record(HASH_A, 'default'), record(HASH_B, 'other'))

    labeled = resolve(session, PlainOperand(text='default'))

    assert labeled.label == 'default'
    assert labeled.suite.hash == HASH_A


def test_plain_ambiguous_name() -> None:
    session = session_with(*DEFAULT_RUNS)

    with pytest.raises(AmbiguousOperandError) as excinfo:
        resolve(session, PlainOperand(text='default'))

    assert str(excinfo.value) == (
        "operand 'default' is ambiguous, candidates:\n"
        '  default:0  2026-09-01 10:00:00  3fa2b1000000\n'
        '  default:1  2026-09-02 10:00:00  9c01de000000\n'
        '  default:2  unknown date  3fa2b2000000'
    )
    assert len(excinfo.value.candidates) == 3


def test_plain_hash_prefix() -> None:
    session = session_with(record(HASH_A, 'x'), record(HASH_B, None))

    labeled = resolve(session, PlainOperand(text='9c01de'))

    assert labeled.label == '9c01de'
    assert labeled.suite.hash == HASH_B


def test_plain_short_prefix_is_not_searched() -> None:
    session = session_with(record(HASH_A, None))

    message = failure(session, PlainOperand(text='3fa2b'), OperandNotFoundError)

    assert message == (
        "operand '3fa2b' not found: no file, run name or hash prefix matches"
    )
    assert session.prefix_lookups == []


def test_plain_ambiguous_prefix() -> None:
    session = session_with(
        record('3fa2b1'.ljust(64, 'a'), 'x'),
        record('3fa2b1'.ljust(64, 'b'), None),
    )

    message = failure(
        session,
        PlainOperand(text='3fa2b1'),
        AmbiguousOperandError,
    )

    assert message.split('\n') == [
        "operand '3fa2b1' is ambiguous, candidates:",
        '  3fa2b1aaaaaa  unknown date  x',
        '  3fa2b1bbbbbb  unknown date  <unnamed>',
    ]


def test_plain_not_hex_not_found() -> None:
    session = session_with(record(HASH_A, 'default'))

    message = failure(
        session,
        PlainOperand(text='nightly'),
        OperandNotFoundError,
    )

    assert message == (
        "operand 'nightly' not found: no file, run name or hash prefix matches"
    )
    assert session.prefix_lookups == []


def test_plain_hex_not_found() -> None:
    session = session_with(record(HASH_A, 'default'))

    failure(session, PlainOperand(text='abcdef'), OperandNotFoundError)

    assert session.prefix_lookups == [('abcdef', None)]


def test_tagged_index() -> None:
    session = session_with(*DEFAULT_RUNS)

    labeled = resolve(session, tagged('default:2', index=2))

    assert labeled.label == 'default:2'
    assert labeled.suite.hash == HASH_C


def test_tagged_index_out_of_range() -> None:
    session = session_with(*DEFAULT_RUNS)

    message = failure(
        session,
        tagged('default:3', index=3),
        OperandNotFoundError,
    )

    assert message == (
        "operand 'default:3' not found: run name 'default' has 3 run(s)"
    )


def test_tagged_prefix() -> None:
    other = record('9c01de'.ljust(64, 'f'), 'x')
    session = session_with(*DEFAULT_RUNS, other)

    labeled = resolve(session, tagged('default:9c01de', hash_prefix='9c01de'))

    assert labeled.label == 'default:9c01de'
    assert labeled.suite.hash == HASH_B


def test_tagged_prefix_not_found() -> None:
    session = session_with(record(HASH_B, 'other'))

    message = failure(
        session,
        tagged('default:9c01de', hash_prefix='9c01de'),
        OperandNotFoundError,
    )

    assert message == (
        "operand 'default:9c01de' not found: "
        "no run named 'default' with hash prefix '9c01de'"
    )


def test_tagged_prefix_ambiguous() -> None:
    session = session_with(*DEFAULT_RUNS)

    message = failure(
        session,
        tagged('default:3fa2b', hash_prefix='3fa2b'),
        AmbiguousOperandError,
    )

    assert message.split('\n')[1:] == [
        '  3fa2b1000000  2026-09-01 10:00:00  default',
        '  3fa2b2000000  unknown date  default',
    ]
