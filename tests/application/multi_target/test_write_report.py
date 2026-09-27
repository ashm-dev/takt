import pytest

from takt.application.multi_target.target_outcome import TargetOutcome
from takt.application.multi_target.target_status import TargetStatus
from takt.application.multi_target.write_report import WriteReport
from takt.domain.model.target import Target

TARGET = Target(name='a', url='sqlite:///a.db', dialect='sqlite')
"""Target shared by every outcome in these tests."""

EXISTING_NAME_ERROR = 'existing_name is only allowed for already_loaded'
"""Error text for ``existing_name`` set on a not already loaded outcome."""

ERROR_TEXT_ERROR = 'error is required for failed and only allowed for failed'
"""Error text for ``error`` missing on failed or set on another status."""


def outcome(
    status: TargetStatus,
    *,
    existing_name: str | None = None,
    error: str | None = None,
) -> TargetOutcome:
    return TargetOutcome(
        target=TARGET,
        status=status,
        existing_name=existing_name,
        error=error,
    )


def test_succeeded_true_for_written_and_already_loaded() -> None:
    report = WriteReport(
        outcomes=(
            outcome(TargetStatus.WRITTEN),
            outcome(TargetStatus.ALREADY_LOADED, existing_name='old'),
        ),
    )

    assert report.succeeded


def test_succeeded_true_for_empty_outcomes() -> None:
    assert WriteReport(outcomes=()).succeeded


@pytest.mark.parametrize(
    'failed',
    [
        outcome(TargetStatus.FAILED, error='boom'),
        outcome(TargetStatus.ROLLED_BACK),
        outcome(TargetStatus.NOT_ATTEMPTED),
    ],
)
def test_succeeded_false_when_any_failed_rolled_back_or_not_attempted(
    failed: TargetOutcome,
) -> None:
    report = WriteReport(outcomes=(outcome(TargetStatus.WRITTEN), failed))

    assert not report.succeeded


def test_outcome_rejects_error_for_non_failed() -> None:
    with pytest.raises(ValueError, match=ERROR_TEXT_ERROR):
        outcome(TargetStatus.WRITTEN, error='boom')


def test_outcome_requires_error_for_failed() -> None:
    with pytest.raises(ValueError, match=ERROR_TEXT_ERROR):
        outcome(TargetStatus.FAILED)


def test_outcome_rejects_existing_name_for_written() -> None:
    with pytest.raises(ValueError, match=EXISTING_NAME_ERROR):
        outcome(TargetStatus.WRITTEN, existing_name='old')
