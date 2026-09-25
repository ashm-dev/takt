"""Handler of ``takt import``."""

import argparse

from takt import api
from takt.cli.error_output import print_error
from takt.cli.exit_code import ExitCode
from takt.cli.report_output import print_import_report


def handle_import(args: argparse.Namespace) -> int:
    """Store an existing result file and print the report.

    :param args: Parsed arguments of ``takt import``.
    :returns: Process exit code.
    """
    report = api.import_results(
        args.path,
        db=args.db,
        target=args.target,
        config=args.config,
        name=args.name,
    )
    print_import_report(report)
    if report.write.succeeded:
        return ExitCode.OK
    print_error('result was not written to all targets')
    return ExitCode.FAILURE
