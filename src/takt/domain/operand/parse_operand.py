"""Parsing of a single compare operand into its typed form."""

import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Final

from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.operand.expand_home import expand_home
from takt.domain.operand.file_operand import FileOperand
from takt.domain.operand.hash_prefix_pattern import HASH_PREFIX_PATTERN
from takt.domain.operand.operand import Operand
from takt.domain.operand.plain_operand import PlainOperand
from takt.domain.operand.tagged_operand import TaggedOperand

_INDEX_PATTERN: Final[re.Pattern[str]] = re.compile(r'[0-9]+')
_FILE_SUFFIXES: Final = ('.json', '.json.gz')
# A bare '/' is not enough: run names such as 'release/3.14' are valid.
_PATH_PREFIXES: Final = ('/', './', '../', '~/')


def parse_operand(
    operand: str | os.PathLike[str],
    is_file: Callable[[Path], bool],
) -> Operand:
    """Parse a single compare operand.

    :param operand: Operand as the user wrote it; a path object always
        names a result file.
    :param is_file: Predicate checking whether a path is an existing
        file; it is called at most once, with the operand path after
        ``~`` expansion (``~name`` of an unknown user stays as written),
        and that expansion may itself read the system user database.
    :returns: The parsed operand.
    :raises OperandNotFoundError: If the operand is empty or malformed, or
        it is a path object or looks like a path, and no such file exists.
    """
    text = os.fspath(operand)
    if text.strip() == '':
        msg = 'operand must not be empty'
        raise OperandNotFoundError(msg)
    path = expand_home(text)
    if is_file(path):
        return FileOperand(text=text, path=path)
    if not isinstance(operand, str) or _looks_like_path(text):
        msg = f'result file not found: {text}'
        raise OperandNotFoundError(msg)
    if ':' not in text:
        return PlainOperand(text=text)
    return _parse_tagged(text)


def _looks_like_path(text: str) -> bool:
    return text.endswith(_FILE_SUFFIXES) or text.startswith(_PATH_PREFIXES)


def _parse_tagged(text: str) -> TaggedOperand:
    name, _, tail = text.partition(':')
    _validate_tag(text=text, name=name, tail=tail)
    if _INDEX_PATTERN.fullmatch(tail) is not None:
        return TaggedOperand(
            text=text,
            name=name,
            index=_run_index(text=text, tail=tail),
            hash_prefix=None,
        )
    return _parse_hash_prefix(text=text, name=name, tail=tail)


def _run_index(*, text: str, tail: str) -> int:
    try:
        return int(tail)
    except ValueError:
        msg = f'invalid operand {text!r}: run index is too large'
        raise OperandNotFoundError(msg) from None


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
