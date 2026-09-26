"""Run benchmarks and import the resulting pyperf result file."""

from takt.application.ports.benchmark_runner import BenchmarkRunner
from takt.application.use_cases.import_report import ImportReport
from takt.application.use_cases.import_request import ImportRequest
from takt.application.use_cases.import_suite import ImportSuite
from takt.application.use_cases.run_request import RunRequest
from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.errors.no_targets_error import NoTargetsError
from takt.domain.model.suite_source import SuiteSource


class RunSuite:
    """Run benchmarks and import the result into every target."""

    def __init__(
        self,
        *,
        runner: BenchmarkRunner,
        importer: ImportSuite,
    ) -> None:
        """Create the use case on top of its ports.

        :param runner: Runs pyperformance or a pyperf script.
        :param importer: Imports the resulting pyperf result file.
        """
        self._runner = runner
        self._importer = importer

    def execute(self, request: RunRequest) -> ImportReport:
        """Run benchmarks and import the produced result file.

        :param request: Runner arguments, targets and the name template.
        :returns: The import report, even when a target write failed.
        :raises NoTargetsError: If ``request.targets`` is empty.
        :raises UsageError: If ``-o``/``--output`` in the runner arguments
            has no value.
        :raises BenchmarkFailedError: If the benchmark process fails.
        :raises InvalidResultError: If the result file cannot be read.
        :raises InvalidRunNameError: If the rendered run name is invalid;
            ``result_path`` then names the result file of the benchmarks.
        """
        if not request.targets:
            raise NoTargetsError
        path = self._runner.run(request.runner_arguments)
        import_request = ImportRequest(
            path=path,
            targets=request.targets,
            name_template=request.name_template,
            source=SuiteSource.RUN,
        )
        try:
            return self._importer.execute(import_request)
        except InvalidRunNameError as error:
            raise InvalidRunNameError(str(error), result_path=path) from error
