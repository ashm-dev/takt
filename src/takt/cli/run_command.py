"""Handler of ``takt run``."""

import argparse
import sys
from pathlib import Path

from takt import api
from takt.cli.error_output import print_error
from takt.cli.exit_code import ExitCode
from takt.cli.report_output import print_import_report
from takt.cli.retry_command import build_retry_command
from takt.domain.errors.benchmark_failed_error import BenchmarkFailedError
from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.naming.literal_template import literal_template


def handle_run(
    args: argparse.Namespace,
    runner_arguments: tuple[str, ...],
) -> int:
    """Run benchmarks, store the result and print the report.

    :param args: Parsed arguments of ``takt run``.
    :param runner_arguments: Arguments passed to pyperformance or pyperf.
    :returns: Process exit code.
    """
    try:
        report = api.run(
            runner_arguments,
            db=args.db,
            target=args.target,
            config=args.config,
            name=args.name,
        )
    except BenchmarkFailedError as error:
        if error.result_path is None:
            raise
        print_error(str(error))
        _print_partial_hint(args, error.result_path)
        return ExitCode.FAILURE
    except InvalidRunNameError as error:
        if error.result_path is None:
            raise
        print_error(str(error))
        sys.stderr.write(
            f'Result was written to {error.result_path}. '
            'Load it with takt import and another --name.\n',
        )
        return ExitCode.USAGE
    print_import_report(report)
    if report.write.succeeded:
        return ExitCode.OK
    print_error('result was not written to all targets')
    # A template with {date} would give the retried result another name.
    name = None if report.name is None else literal_template(report.name)
    retry = build_retry_command(args, report.result_path, name)
    sys.stderr.write(f'Retry without re-running benchmarks: {retry}\n')
    return ExitCode.FAILURE


def _print_partial_hint(args: argparse.Namespace, result_path: Path) -> None:
    retry = build_retry_command(args, result_path, args.name)
    sys.stderr.write(
        f'Partial result was written to {result_path}. '
        f'Load it without re-running benchmarks: {retry}\n',
    )
