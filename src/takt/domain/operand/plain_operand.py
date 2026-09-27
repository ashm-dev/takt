"""Compare operand without a ':' and without a matching file."""

import string
from dataclasses import dataclass

from takt.domain.operand.hash_prefix_pattern import HASH_PREFIX_PATTERN

_HEX_DIGITS = frozenset(string.hexdigits)
"""Hex digit characters in both letter cases."""

_HEX_LETTERS = _HEX_DIGITS - frozenset(string.digits)
"""Hex letters ``a`` to ``f`` in both cases."""


@dataclass(frozen=True, kw_only=True)
class PlainOperand:
    """Compare operand tried first as a run name, then as a hash prefix."""

    text: str
    """Operand text as the user wrote it."""

    def is_hash_prefix(self) -> bool:
        """Tell whether the text is searched as a hash prefix.

        :returns: Whether it has 6 to 64 lowercase hex characters.
        """
        return HASH_PREFIX_PATTERN.fullmatch(self.text) is not None

    def looks_like_hash(self) -> bool:
        """Tell whether the text is hex and mixes digits with letters.

        :returns: Whether the user probably meant a hash prefix.
        """
        characters = set(self.text)
        # Names such as 314 or cafe are more likely run names than hashes.
        return (
            characters <= _HEX_DIGITS
            and not characters.isdisjoint(string.digits)
            and not characters.isdisjoint(_HEX_LETTERS)
        )
