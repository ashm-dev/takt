from pathlib import Path

import pytest

from takt.domain.errors.ambiguous_operand_error import AmbiguousOperandError
from takt.domain.errors.benchmark_failed_error import BenchmarkFailedError
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.execution_error import ExecutionError
from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.errors.missing_driver_error import MissingDriverError
from takt.domain.errors.no_common_benchmarks_error import (
    NoCommonBenchmarksError,
)
from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.errors.takt_error import TaktError
from takt.domain.errors.unsupported_dialect_error import (
    UnsupportedDialectError,
)
from takt.domain.errors.usage_error import UsageError
from takt.domain.model.suite_summary import SuiteSummary


@pytest.mark.parametrize(
    ('error_class', 'parent', 'exit_code'),
    [
        (UsageError, TaktError, 2),
        (ExecutionError, TaktError, 1),
        (ConfigurationError, UsageError, 2),
        (UnsupportedDialectError, ConfigurationError, 2),
        (MissingDriverError, ConfigurationError, 2),
        (InvalidRunNameError, UsageError, 2),
        (InvalidResultError, ExecutionError, 1),
        (OperandNotFoundError, ExecutionError, 1),
        (NoCommonBenchmarksError, ExecutionError, 1),
    ],
)
def test_error_parent_and_exit_code(
    error_class: type[TaktError],
    parent: type[TaktError],
    exit_code: int,
) -> None:
    error = error_class('broken')

    assert isinstance(error, parent)
    assert error.exit_code == exit_code
    assert str(error) == 'broken'


def test_takt_error_exit_code() -> None:
    assert TaktError('broken').exit_code == 1


def test_ambiguous_operand_error_keeps_candidates() -> None:
    candidates = (
        SuiteSummary(hash='a' * 64, name='default', result_date=None),
    )

    error = AmbiguousOperandError('ambiguous', candidates=candidates)

    assert isinstance(error, ExecutionError)
    assert error.candidates == candidates
    assert str(error) == 'ambiguous'


def test_benchmark_failed_error_keeps_return_code() -> None:
    error = BenchmarkFailedError('failed', return_code=3)

    assert isinstance(error, ExecutionError)
    assert error.return_code == 3
    assert error.exit_code == 1
    assert error.result_path is None


def test_benchmark_failed_error_keeps_result_path() -> None:
    error = BenchmarkFailedError(
        'failed',
        return_code=1,
        result_path=Path('r.json'),
    )

    assert error.result_path == Path('r.json')
