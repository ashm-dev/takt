"""Import reports shared by the CLI tests."""

from pathlib import Path

from takt.application.multi_target.target_outcome import TargetOutcome
from takt.application.multi_target.target_status import TargetStatus
from takt.application.multi_target.write_report import WriteReport
from takt.application.use_cases.import_report import ImportReport
from takt.domain.model.target import Target

LOCAL = Target(name='local', url='sqlite:///a.db', dialect='sqlite')
MARIA = Target(
    name=None,
    url='mariadb+pymysql://u:secret@h/db',
    dialect='mariadb',
)


def outcome(
    target: Target,
    status: TargetStatus,
    *,
    existing_name: str | None = None,
    error: str | None = None,
) -> TargetOutcome:
    return TargetOutcome(
        target=target,
        status=status,
        existing_name=existing_name,
        error=error,
    )


def report(
    *outcomes: TargetOutcome,
    name: str | None = 'default',
) -> ImportReport:
    return ImportReport(
        result_path=Path('r.json'),
        suite_hash='3fa2b1c4d5e6'.ljust(64, '0'),
        name=name,
        write=WriteReport(outcomes=outcomes),
    )


OK_REPORT = report(outcome(LOCAL, TargetStatus.WRITTEN))
FAILED_REPORT = report(
    outcome(LOCAL, TargetStatus.ROLLED_BACK),
    outcome(MARIA, TargetStatus.FAILED, error='connection refused'),
)
