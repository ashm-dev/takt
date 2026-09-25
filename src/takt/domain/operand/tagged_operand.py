"""Compare operand made of a run name and an index or a hash prefix."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class TaggedOperand:
    """Compare operand made of a run name and an index or a hash prefix.

    :ivar text: Operand text as the user wrote it.
    :ivar name: Run name before the ``:``.
    :ivar index: Zero-based position within the named run's suites.
    :ivar hash_prefix: Lowercase hexadecimal prefix of a suite hash.
    """

    text: str
    name: str
    index: int | None
    hash_prefix: str | None

    def __post_init__(self) -> None:
        """Validate the tagged operand invariant.

        :raises ValueError: If not exactly one of ``index`` and
            ``hash_prefix`` is set.
        """
        if (self.index is None) == (self.hash_prefix is None):
            msg = 'exactly one of index and hash_prefix must be set'
            raise ValueError(msg)
