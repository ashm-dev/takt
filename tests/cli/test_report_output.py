import pytest

from takt.application.multi_target.target_status import TargetStatus
from takt.application.use_cases.import_report import ImportReport
from takt.cli.report_output import print_import_report
from tests.cli.reports import FAILED_REPORT, LOCAL, OK_REPORT, outcome, report


def printed_lines(
    capsys: pytest.CaptureFixture[str],
    printed: ImportReport,
) -> list[str]:
    print_import_report(printed)
    return capsys.readouterr().out.splitlines()


def test_ok_report(capsys: pytest.CaptureFixture[str]) -> None:
    print_import_report(OK_REPORT)

    assert capsys.readouterr().out == (
        'Result 3fa2b1c4d5e6 (default) from r.json\n  local: written\n'
    )


def test_failed_report_hides_password(
    capsys: pytest.CaptureFixture[str],
) -> None:
    lines = printed_lines(capsys, FAILED_REPORT)

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


@pytest.mark.parametrize(
    ('existing', 'header'),
    [
        (('old', 'old'), 'Result 3fa2b1c4d5e6 (old) from r.json'),
        ((None, None), 'Result 3fa2b1c4d5e6 (unnamed) from r.json'),
        (('old', 'older'), 'Result 3fa2b1c4d5e6 from r.json'),
    ],
)
def test_loaded_everywhere_shows_stored_name(
    capsys: pytest.CaptureFixture[str],
    existing: tuple[str | None, str | None],
    header: str,
) -> None:
    loaded = report(
        *(
            outcome(LOCAL, TargetStatus.ALREADY_LOADED, existing_name=name)
            for name in existing
        ),
        name='requested',
    )

    assert printed_lines(capsys, loaded)[0] == header


def test_mixed_outcomes_show_requested_name(
    capsys: pytest.CaptureFixture[str],
) -> None:
    mixed = report(
        outcome(LOCAL, TargetStatus.ALREADY_LOADED, existing_name='old'),
        outcome(LOCAL, TargetStatus.WRITTEN),
        name='requested',
    )

    assert printed_lines(capsys, mixed)[0] == (
        'Result 3fa2b1c4d5e6 (requested) from r.json'
    )
