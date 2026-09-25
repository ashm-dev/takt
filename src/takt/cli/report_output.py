"""Printing of an import report to standard output."""

import sys
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from takt.application.multi_target.target_outcome import TargetOutcome
from takt.application.multi_target.target_status import TargetStatus
from takt.application.use_cases.import_report import ImportReport

_HASH_PREFIX_LENGTH: Final = 12
_PLAIN_TEXTS: Final[Mapping[TargetStatus, str]] = MappingProxyType(
    {
        TargetStatus.WRITTEN: 'written',
        TargetStatus.ROLLED_BACK: 'rolled back',
        TargetStatus.NOT_ATTEMPTED: 'not attempted',
    }
)


def print_import_report(report: ImportReport) -> None:
    """Print the result line and one line per target outcome.

    :param report: Report returned by ``run`` or ``import_results``.
    """
    short_hash = report.suite_hash[:_HASH_PREFIX_LENGTH]
    name = report.name or 'unnamed'
    sys.stdout.write(
        f'Result {short_hash} ({name}) from {report.result_path}\n',
    )
    for outcome in report.write.outcomes:
        target = outcome.target.display()
        sys.stdout.write(f'  {target}: {_status_text(outcome)}\n')


def _status_text(outcome: TargetOutcome) -> str:
    if outcome.status is TargetStatus.FAILED:
        return f'failed: {outcome.error}'
    if outcome.status is TargetStatus.ALREADY_LOADED:
        if outcome.existing_name is None:
            return 'already loaded (unnamed)'
        return f"already loaded as '{outcome.existing_name}'"
    return _PLAIN_TEXTS[outcome.status]
