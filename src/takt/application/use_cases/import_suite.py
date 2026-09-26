"""Import a pyperf result file into database targets."""

from datetime import datetime

from takt.application.multi_target.multi_target_writer import MultiTargetWriter
from takt.application.multi_target.write_report import WriteReport
from takt.application.ports.clock import Clock
from takt.application.ports.result_reader import ResultReader
from takt.application.use_cases.import_report import ImportReport
from takt.application.use_cases.import_request import ImportRequest
from takt.domain.errors.no_targets_error import NoTargetsError
from takt.domain.errors.write_interrupted_error import WriteInterruptedError
from takt.domain.model.suite import Suite
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.naming.name_values import NameValues


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
        :raises NoTargetsError: If ``request.targets`` is empty.
        :raises InvalidResultError: If the result file cannot be read.
        :raises InvalidRunNameError: If the rendered run name is invalid.
        :raises KeyboardInterrupt: On Ctrl+C during the database write; its
            ``__cause__`` is a ``WriteInterruptedError`` with the result
            file and the run name.
        """
        if not request.targets:
            raise NoTargetsError
        suite = self._reader.read(request.path)
        now = self._clock.now()
        name = self._render_name(request, suite, now)
        record = SuiteRecord(
            suite=suite,
            name=name,
            source=request.source,
            loaded_at=now,
        )
        return ImportReport(
            result_path=request.path,
            suite_hash=suite.hash,
            name=name,
            write=self._write(record, request),
        )

    def _write(
        self,
        record: SuiteRecord,
        request: ImportRequest,
    ) -> WriteReport:
        try:
            return self._writer.write(record, request.targets)
        except KeyboardInterrupt as interrupt:
            # mypyc drops the cause of raise ... from, so it is set here.
            interrupt.__cause__ = WriteInterruptedError(
                request.path,
                record.name,
            )
            raise

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
