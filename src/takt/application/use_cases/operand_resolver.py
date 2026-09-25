"""Resolution of compare operands into labeled suites."""

import re

from takt.application.ports.result_reader import ResultReader
from takt.application.ports.target_session import TargetSession
from takt.domain.compare.labeled_suite import LabeledSuite
from takt.domain.errors.ambiguous_operand_error import AmbiguousOperandError
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.model.suite_summary import SuiteSummary
from takt.domain.operand.file_operand import FileOperand
from takt.domain.operand.operand import Operand
from takt.domain.operand.plain_operand import PlainOperand
from takt.domain.operand.tagged_operand import TaggedOperand

_HASH_PREFIX_PATTERN = re.compile('[0-9a-f]{6,64}')
_SHORT_HASH_LENGTH = 12

_Matches = tuple[SuiteSummary, ...]


class OperandResolver:
    """Turn parsed compare operands into labeled suites."""

    def __init__(
        self,
        *,
        reader: ResultReader,
        session: TargetSession | None,
    ) -> None:
        """Create the resolver.

        :param reader: Reads result files.
        :param session: Open database session, or ``None`` without a target.
        """
        self._reader = reader
        self._session = session

    def resolve(self, operand: Operand) -> LabeledSuite:
        """Load the suite behind the operand.

        :param operand: Parsed operand.
        :returns: The suite labeled with the operand text.
        :raises ConfigurationError: If a database operand has no session.
        :raises OperandNotFoundError: If nothing matches the operand.
        :raises AmbiguousOperandError: If several stored runs match.
        :raises InvalidResultError: If the result file cannot be read.
        """
        if isinstance(operand, FileOperand):
            return LabeledSuite(
                label=operand.text,
                suite=self._reader.read(operand.path),
            )
        session = self._session
        if session is None:
            msg = (
                f"operand '{operand.text}' is not a file "
                'and no database target is configured'
            )
            raise ConfigurationError(msg)
        if isinstance(operand, PlainOperand):
            summary = self._find_plain(session, operand)
        elif operand.index is None:
            summary = self._find_tagged_prefix(session, operand)
        else:
            summary = self._find_tagged_index(session, operand, operand.index)
        return LabeledSuite(
            label=operand.text,
            suite=session.get(summary.hash).suite,
        )

    def _find_plain(
        self,
        session: TargetSession,
        operand: PlainOperand,
    ) -> SuiteSummary:
        text = operand.text
        matches = session.find_by_name(text)
        if len(matches) > 1:
            raise _ambiguous(text, _name_lines(text, matches), matches)
        if not matches and _HASH_PREFIX_PATTERN.fullmatch(text) is not None:
            matches = session.find_by_hash_prefix(text, None)
            if len(matches) > 1:
                raise _ambiguous(text, _prefix_lines(matches), matches)
        if matches:
            return matches[0]
        msg = (
            f"operand '{text}' not found: "
            'no file, run name or hash prefix matches'
        )
        raise OperandNotFoundError(msg)

    def _find_tagged_index(
        self,
        session: TargetSession,
        operand: TaggedOperand,
        index: int,
    ) -> SuiteSummary:
        matches = session.find_by_name(operand.name)
        if 0 <= index < len(matches):
            return matches[index]
        count = len(matches)
        msg = (
            f"operand '{operand.text}' not found: "
            f"run name '{operand.name}' has {count} run(s)"
        )
        raise OperandNotFoundError(msg)

    def _find_tagged_prefix(
        self,
        session: TargetSession,
        operand: TaggedOperand,
    ) -> SuiteSummary:
        prefix = operand.hash_prefix or ''
        matches = session.find_by_hash_prefix(prefix, operand.name)
        if len(matches) > 1:
            raise _ambiguous(operand.text, _prefix_lines(matches), matches)
        if matches:
            return matches[0]
        msg = (
            f"operand '{operand.text}' not found: "
            f"no run named '{operand.name}' with hash prefix '{prefix}'"
        )
        raise OperandNotFoundError(msg)


def _name_lines(text: str, matches: _Matches) -> list[str]:
    return [
        _candidate(
            f'{text}:{index}',
            _date(summary),
            summary.hash[:_SHORT_HASH_LENGTH],
        )
        for index, summary in enumerate(matches)
    ]


def _prefix_lines(matches: _Matches) -> list[str]:
    return [
        _candidate(
            summary.hash[:_SHORT_HASH_LENGTH],
            _date(summary),
            summary.name or '<unnamed>',
        )
        for summary in matches
    ]


def _candidate(*columns: str) -> str:
    return '  '.join(('', *columns))


def _ambiguous(
    text: str,
    lines: list[str],
    matches: _Matches,
) -> AmbiguousOperandError:
    header = f"operand '{text}' is ambiguous, candidates:"
    return AmbiguousOperandError(
        '\n'.join((header, *lines)),
        candidates=tuple(matches),
    )


def _date(summary: SuiteSummary) -> str:
    if summary.result_date is None:
        return 'unknown date'
    return summary.result_date.isoformat(sep=' ')
