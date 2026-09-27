"""Run pyperformance and pyperf benchmarks and store results in SQL."""

from importlib.metadata import version
from typing import Final

from takt.api import compare, import_results, run
from takt.application.multi_target.target_outcome import TargetOutcome
from takt.application.multi_target.target_status import TargetStatus
from takt.application.multi_target.write_report import WriteReport
from takt.application.use_cases.import_report import ImportReport
from takt.domain.compare.compare_table import CompareTable
from takt.domain.errors.execution_error import ExecutionError
from takt.domain.errors.takt_error import TaktError
from takt.domain.errors.usage_error import UsageError

__version__: Final[str] = version('takt-py')
"""Version of the installed ``takt-py`` distribution."""

__all__ = (
    'run',
    'import_results',
    'compare',
    'ImportReport',
    'WriteReport',
    'TargetOutcome',
    'TargetStatus',
    'CompareTable',
    'TaktError',
    'UsageError',
    'ExecutionError',
    '__version__',
)
"""Names that make up the public API of the package."""
