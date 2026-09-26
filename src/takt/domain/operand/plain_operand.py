"""Compare operand without a ':' and without a matching file."""

import string
from dataclasses import dataclass

from takt.domain.operand.hash_prefix_pattern import HASH_PREFIX_PATTERN

_HEX_DIGITS = frozenset(string.hexdigits)


@dataclass(frozen=True, kw_only=True)
class PlainOperand:
    """Compare operand tried first as a run name, then as a hash prefix.

    :ivar text: Operand text as the user wrote it.
    """

    text: str

    def is_hash_prefix(self) -> bool:
        """Tell whether the text is searched as a hash prefix.

        :returns: Whether it has 6 to 64 lowercase hex characters.
        """
        return HASH_PREFIX_PATTERN.fullmatch(self.text) is not None

    def looks_like_hash(self) -> bool:
        """Tell whether the text has only hex digits, in any case.

        :returns: Whether the user probably meant a hash prefix.
        """
        return set(self.text) <= _HEX_DIGITS
