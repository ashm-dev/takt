from collections.abc import Callable
from pathlib import Path

import pytest

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


def _parse_error(
    text: str,
    is_file: Callable[[Path], bool] = never_file,
) -> str:
    try:
        parse_operand(text, is_file)
    except OperandNotFoundError as error:
        return str(error)
    msg = 'expected OperandNotFoundError'
    raise AssertionError(msg)


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
    assert _parse_error(text) == 'operand must not be empty'


def test_missing_name() -> None:
    assert _parse_error(':1') == (
        "invalid operand ':1': missing run name before ':'"
    )


def test_missing_tail() -> None:
    assert _parse_error('default:') == (
        "invalid operand 'default:': missing value after ':'"
    )


def test_two_colons() -> None:
    assert _parse_error('a:b:c') == (
        "invalid operand 'a:b:c': only one ':' is allowed"
    )


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
    expected_suffix = (
        'expected a number or a hash prefix of at least 6 lowercase '
        "hex characters after ':'"
    )

    assert _parse_error(text).endswith(expected_suffix)


def test_tagged_operand_invariant() -> None:
    expected = 'exactly one of index and hash_prefix must be set'

    with pytest.raises(ValueError, match=expected):
        TaggedOperand(text='x', name='x', index=None, hash_prefix=None)

    with pytest.raises(ValueError, match=expected):
        TaggedOperand(text='x', name='x', index=1, hash_prefix='3fa2b1')


def test_is_file_called_with_expanded_path() -> None:
    expanded = Path('~/x').expanduser()
    is_file = _RecordingIsFile()

    parse_operand('~/x', is_file)

    assert is_file.calls == [expanded]
