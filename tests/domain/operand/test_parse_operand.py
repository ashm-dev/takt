import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from tests.domain.exact_pattern import exact_pattern

from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.operand.file_operand import FileOperand
from takt.domain.operand.parse_operand import parse_operand
from takt.domain.operand.plain_operand import PlainOperand
from takt.domain.operand.tagged_operand import TaggedOperand


def never_file(_path: Path) -> bool:
    return False


def only(expected: Path) -> Callable[[Path], bool]:
    return lambda path: path == expected


class _RecordingIsFile:
    """Predicate that records every path it was asked about."""

    def __init__(self) -> None:
        self.calls: list[Path] = []

    def __call__(self, path: Path) -> bool:
        self.calls.append(path)
        return False


def test_file_wins() -> None:
    operand = parse_operand('res.json', only(Path('res.json')))

    assert operand == FileOperand(text='res.json', path=Path('res.json'))


def test_file_with_colon_wins() -> None:
    operand = parse_operand('default:1', only(Path('default:1')))

    assert operand == FileOperand(text='default:1', path=Path('default:1'))


def test_home_is_expanded() -> None:
    expanded = Path('~/r.json').expanduser()

    operand = parse_operand('~/r.json', only(expanded))

    assert isinstance(operand, FileOperand)
    assert operand.path == expanded
    assert operand.text == '~/r.json'


def test_unknown_user_home_is_run_name() -> None:
    is_file = _RecordingIsFile()

    operand = parse_operand('~takt-no-such-user', is_file)

    assert operand == PlainOperand(text='~takt-no-such-user')
    assert is_file.calls == [Path('~takt-no-such-user')]


def test_unknown_user_home_file_wins() -> None:
    path = Path('~takt-no-such-user')

    operand = parse_operand('~takt-no-such-user', only(path))

    assert operand == FileOperand(text='~takt-no-such-user', path=path)


def test_home_with_nul_byte_is_run_name() -> None:
    is_file = _RecordingIsFile()

    operand = parse_operand('~takt\x00user', is_file)

    assert operand == PlainOperand(text='~takt\x00user')
    assert is_file.calls == [Path('~takt\x00user')]


@pytest.mark.parametrize(
    'text',
    ['dir/x.json', 'bench-10:15.json', 'r.json.gz', './x', '../x', '/x', '~/x'],
)
def test_missing_result_file(text: str) -> None:
    message = f'result file not found: {text}'

    with pytest.raises(OperandNotFoundError, match=exact_pattern(message)):
        parse_operand(text, never_file)


def test_name_with_slash_is_run_name() -> None:
    operand = parse_operand('release/3.14', never_file)

    assert operand == PlainOperand(text='release/3.14')


@pytest.mark.parametrize(
    ('text', 'is_prefix', 'looks_like_hash'),
    [
        ('3fa2b1', True, True),
        ('3fa2b', False, True),
        ('3FA2B1', False, True),
        ('nightly', False, False),
        ('314', False, False),
        ('cafe', False, False),
    ],
)
def test_plain_operand_hash_checks(
    text: str,
    *,
    is_prefix: bool,
    looks_like_hash: bool,
) -> None:
    operand = PlainOperand(text=text)

    assert operand.is_hash_prefix() is is_prefix
    assert operand.looks_like_hash() is looks_like_hash


def test_plain_name() -> None:
    operand = parse_operand('default 01.01.01', never_file)

    assert operand == PlainOperand(text='default 01.01.01')


def test_plain_hash_like() -> None:
    operand = parse_operand('3fa2b1', never_file)

    assert operand == PlainOperand(text='3fa2b1')


@pytest.mark.parametrize(
    ('text', 'index'),
    [
        ('default:0', 0),
        ('default:2', 2),
        ('default:007', 7),
        ('default:123456', 123456),
    ],
)
def test_name_index(text: str, index: int) -> None:
    operand = parse_operand(text, never_file)

    assert operand == TaggedOperand(
        text=text,
        name='default',
        index=index,
        hash_prefix=None,
    )


def test_name_hash_prefix() -> None:
    operand = parse_operand('default:3fa2b1', never_file)

    assert operand == TaggedOperand(
        text='default:3fa2b1',
        name='default',
        index=None,
        hash_prefix='3fa2b1',
    )


def test_name_hash_prefix_full_length() -> None:
    hash_prefix = 'a' * 64
    text = f'default:{hash_prefix}'

    operand = parse_operand(text, never_file)

    assert operand == TaggedOperand(
        text=text,
        name='default',
        index=None,
        hash_prefix=hash_prefix,
    )


def test_name_with_spaces() -> None:
    operand = parse_operand('jit+pgo 01.02.03:1', never_file)

    assert operand == TaggedOperand(
        text='jit+pgo 01.02.03:1',
        name='jit+pgo 01.02.03',
        index=1,
        hash_prefix=None,
    )


@pytest.mark.parametrize('text', ['', '   '])
def test_empty_operand(text: str) -> None:
    message = 'operand must not be empty'

    with pytest.raises(OperandNotFoundError, match=exact_pattern(message)):
        parse_operand(text, never_file)


def test_missing_name() -> None:
    message = "invalid operand ':1': missing run name before ':'"

    with pytest.raises(OperandNotFoundError, match=exact_pattern(message)):
        parse_operand(':1', never_file)


def test_missing_tail() -> None:
    message = "invalid operand 'default:': missing value after ':'"

    with pytest.raises(OperandNotFoundError, match=exact_pattern(message)):
        parse_operand('default:', never_file)


@pytest.fixture
def int_digit_limit() -> Iterator[int]:
    """Pin the interpreter limit on digits that ``int()`` accepts."""
    previous = sys.get_int_max_str_digits()
    limit = 4300
    sys.set_int_max_str_digits(limit)
    yield limit
    sys.set_int_max_str_digits(previous)


def test_too_large_index(int_digit_limit: int) -> None:
    digits = '1' * (int_digit_limit + 1)
    text = f'default:{digits}'
    message = f'invalid operand {text!r}: run index is too large'

    with pytest.raises(OperandNotFoundError, match=exact_pattern(message)):
        parse_operand(text, never_file)


def test_two_colons() -> None:
    message = "invalid operand 'a:b:c': only one ':' is allowed"

    with pytest.raises(OperandNotFoundError, match=exact_pattern(message)):
        parse_operand('a:b:c', never_file)


_TOO_LONG_HEX_TAIL = 'a' * 65
_TOO_LONG_HASH_PREFIX = f'default:{_TOO_LONG_HEX_TAIL}'


@pytest.mark.parametrize(
    'text',
    [
        'default:3fa2b',
        'default:ABCDEF',
        'default:xyz123',
        _TOO_LONG_HASH_PREFIX,
    ],
)
def test_bad_tail(text: str) -> None:
    message = (
        f'invalid operand {text!r}: expected a number or a hash prefix '
        "of at least 6 lowercase hex characters after ':'"
    )

    with pytest.raises(OperandNotFoundError, match=exact_pattern(message)):
        parse_operand(text, never_file)


def test_tagged_operand_invariant() -> None:
    expected = 'exactly one of index and hash_prefix must be set'

    with pytest.raises(ValueError, match=expected):
        TaggedOperand(text='x', name='x', index=None, hash_prefix=None)

    with pytest.raises(ValueError, match=expected):
        TaggedOperand(text='x', name='x', index=1, hash_prefix='3fa2b1')


def test_is_file_called_with_expanded_path() -> None:
    expanded = Path('~/x').expanduser()
    is_file = _RecordingIsFile()

    with pytest.raises(OperandNotFoundError):
        parse_operand('~/x', is_file)

    assert is_file.calls == [expanded]
