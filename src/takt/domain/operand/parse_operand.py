"""Parsing of a single compare operand into its typed form."""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Final

from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.operand.file_operand import FileOperand
from takt.domain.operand.hash_prefix_pattern import HASH_PREFIX_PATTERN
from takt.domain.operand.operand import Operand
from takt.domain.operand.plain_operand import PlainOperand
from takt.domain.operand.tagged_operand import TaggedOperand

_INDEX_PATTERN: Final[re.Pattern[str]] = re.compile(r'[0-9]+')


def parse_operand(text: str, is_file: Callable[[Path], bool]) -> Operand:
    """Parse a single compare operand.

    :param text: Operand text as the user wrote it on the command line.
    :param is_file: Predicate checking whether a path is an existing
        file; never called by this function on its own, only through
        this callback.
    :returns: The parsed operand.
    :raises OperandNotFoundError: If the operand is empty or malformed.
    """
    if text.strip() == '':
        msg = 'operand must not be empty'
        raise OperandNotFoundError(msg)
    path = Path(text).expanduser()
    if is_file(path):
        return FileOperand(text=text, path=path)
    if ':' not in text:
        return PlainOperand(text=text)
    return _parse_tagged(text)


def _parse_tagged(text: str) -> TaggedOperand:
    name, _, tail = text.partition(':')
    _validate_tag(text=text, name=name, tail=tail)
    if _INDEX_PATTERN.fullmatch(tail) is not None:
        return TaggedOperand(
            text=text,
            name=name,
            index=int(tail),
            hash_prefix=None,
        )
    return _parse_hash_prefix(text=text, name=name, tail=tail)


def _validate_tag(*, text: str, name: str, tail: str) -> None:
    if name == '':
        msg = f"invalid operand {text!r}: missing run name before ':'"
        raise OperandNotFoundError(msg)
    if tail == '':
        msg = f"invalid operand {text!r}: missing value after ':'"
        raise OperandNotFoundError(msg)
    if ':' in tail:
        msg = f"invalid operand {text!r}: only one ':' is allowed"
        raise OperandNotFoundError(msg)


def _parse_hash_prefix(*, text: str, name: str, tail: str) -> TaggedOperand:
    if HASH_PREFIX_PATTERN.fullmatch(tail) is not None:
        return TaggedOperand(
            text=text,
            name=name,
            index=None,
            hash_prefix=tail,
        )
    msg = (
        f'invalid operand {text!r}: expected a number or a hash prefix '
        "of at least 6 lowercase hex characters after ':'"
    )
    raise OperandNotFoundError(msg)
