"""Import a pyperf result file into database targets."""

from datetime import datetime

from takt.application.multi_target.multi_target_writer import MultiTargetWriter
from takt.application.ports.clock import Clock
from takt.application.ports.result_reader import ResultReader
from takt.application.use_cases.import_report import ImportReport
from takt.application.use_cases.import_request import ImportRequest
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.model.suite import Suite
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.naming.name_values import NameValues

_NO_TARGETS_MESSAGE = (
    'no database targets configured: use --db, --target, TAKT_DB or takt.toml'
)


class ImportSuite:
    """Load a pyperf result file and store it in every target."""

    def __init__(
        self,
        *,
        reader: ResultReader,
        writer: MultiTargetWriter,
        clock: Clock,
    ) -> None:
        """Create the use case on top of its ports.

        :param reader: Reads the pyperf result file.
        :param writer: Writes the suite to every target.
        :param clock: Source of the import time.
        """
        self._reader = reader
        self._writer = writer
        self._clock = clock

    def execute(self, request: ImportRequest) -> ImportReport:
        """Read, name and store the suite described by the request.

        :param request: What to import and where.
        :returns: The import report, even when a target write failed.
        :raises ConfigurationError: If ``request.targets`` is empty.
        :raises InvalidResultError: If the result file cannot be read.
        :raises InvalidRunNameError: If the rendered run name is invalid.
        """
        if not request.targets:
            raise ConfigurationError(_NO_TARGETS_MESSAGE)
        suite = self._reader.read(request.path)
        now = self._clock.now()
        name = self._render_name(request, suite, now)
        record = SuiteRecord(
            suite=suite,
            name=name,
            source=request.source,
            loaded_at=now,
        )
        write = self._writer.write(record, request.targets)
        return ImportReport(
            result_path=request.path,
            suite_hash=suite.hash,
            name=name,
            write=write,
        )

    def _render_name(
        self,
        request: ImportRequest,
        suite: Suite,
        now: datetime,
    ) -> str | None:
        if request.name_template is None:
            return None
        first_run = suite.benchmarks[0].runs[0]
        first = first_run.metadata
        return request.name_template.render(
            NameValues(
                now=now,
                result_path=request.path,
                python_version=first.python_version,
                hostname=first.hostname,
                suite_hash=suite.hash,
            ),
        )
