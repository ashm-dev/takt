from pathlib import Path

import pytest

from takt.application.multi_target.target_outcome import TargetOutcome
from takt.application.multi_target.target_status import TargetStatus
from takt.application.multi_target.write_report import WriteReport
from takt.application.use_cases.import_report import ImportReport
from takt.cli.report_output import print_import_report
from takt.domain.model.target import Target

SUITE_HASH = '3fa2b1c4d5e6'.ljust(64, '0')
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
        suite_hash=SUITE_HASH,
        name=name,
        write=WriteReport(outcomes=outcomes),
    )


def printed_lines(
    capsys: pytest.CaptureFixture[str],
    printed: ImportReport,
) -> list[str]:
    print_import_report(printed)
    return capsys.readouterr().out.splitlines()


def test_ok_report(capsys: pytest.CaptureFixture[str]) -> None:
    print_import_report(report(outcome(LOCAL, TargetStatus.WRITTEN)))

    assert capsys.readouterr().out == (
        'Result 3fa2b1c4d5e6 (default) from r.json\n  local: written\n'
    )


def test_failed_report_hides_password(
    capsys: pytest.CaptureFixture[str],
) -> None:
    failed = report(
        outcome(LOCAL, TargetStatus.ROLLED_BACK),
        outcome(MARIA, TargetStatus.FAILED, error='connection refused'),
    )

    lines = printed_lines(capsys, failed)

    assert lines[1] == '  local: rolled back'
    assert lines[2] == (
        '  mariadb+pymysql://u:***@h/db: failed: connection refused'
    )


def test_already_loaded(capsys: pytest.CaptureFixture[str]) -> None:
    loaded = report(
        outcome(LOCAL, TargetStatus.ALREADY_LOADED, existing_name='old'),
        outcome(LOCAL, TargetStatus.ALREADY_LOADED),
    )

    lines = printed_lines(capsys, loaded)

    assert lines[1] == "  local: already loaded as 'old'"
    assert lines[2] == '  local: already loaded (unnamed)'


def test_unnamed_result(capsys: pytest.CaptureFixture[str]) -> None:
    unnamed = report(outcome(LOCAL, TargetStatus.WRITTEN), name=None)

    lines = printed_lines(capsys, unnamed)

    assert '(unnamed)' in lines[0]
