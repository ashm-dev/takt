"""Handler of ``takt run``."""

import argparse
import sys

from takt import api
from takt.cli.error_output import print_error
from takt.cli.exit_code import ExitCode
from takt.cli.report_output import print_import_report
from takt.cli.retry_command import build_retry_command


def handle_run(
    args: argparse.Namespace,
    runner_arguments: tuple[str, ...],
) -> int:
    """Run benchmarks, store the result and print the report.

    :param args: Parsed arguments of ``takt run``.
    :param runner_arguments: Arguments passed to pyperformance or pyperf.
    :returns: Process exit code.
    """
    report = api.run(
        runner_arguments,
        db=args.db,
        target=args.target,
        config=args.config,
        name=args.name,
    )
    print_import_report(report)
    if report.write.succeeded:
        return ExitCode.OK
    print_error('result was not written to all targets')
    retry = build_retry_command(args, report.result_path)
    sys.stderr.write(f'Retry without re-running benchmarks: {retry}\n')
    return ExitCode.FAILURE
