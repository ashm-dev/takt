"""Handler of ``takt run``."""

import argparse
import sys
from pathlib import Path

from takt import api
from takt.cli.error_output import print_error
from takt.cli.exit_code import ExitCode
from takt.cli.report_output import print_import_report
from takt.cli.retry_command import (
    build_retry_command,
    build_retry_command_for_name,
)
from takt.domain.errors.benchmark_failed_error import BenchmarkFailedError
from takt.domain.errors.benchmark_interrupted_error import (
    BenchmarkInterruptedError,
)
from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.errors.write_interrupted_error import WriteInterruptedError


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
    except KeyboardInterrupt as interrupt:
        return _print_interrupt_hint(args, interrupt)
    except InvalidRunNameError as error:
        return _print_late_name_error(error)
    print_import_report(report)
    if report.write.succeeded:
        return ExitCode.OK
    print_error('result was not written to all targets')
    retry = build_retry_command_for_name(args, report.result_path, report.name)
    sys.stderr.write(f'Retry without re-running benchmarks: {retry}\n')
    return ExitCode.FAILURE


def _print_partial_hint(args: argparse.Namespace, result_path: Path) -> None:
    retry = build_retry_command(args, result_path, args.name)
    sys.stderr.write(
        f'Partial result was written to {result_path}. '
        f'Load it without re-running benchmarks: {retry}\n',
    )


def _print_interrupt_hint(
    args: argparse.Namespace,
    interrupt: KeyboardInterrupt,
) -> int:
    cause = interrupt.__cause__
    if isinstance(cause, BenchmarkInterruptedError):
        _print_partial_hint(args, cause.result_path)
    elif isinstance(cause, WriteInterruptedError):
        retry = build_retry_command_for_name(
            args,
            cause.result_path,
            cause.name,
        )
        sys.stderr.write(
            f'Result was written to {cause.result_path}. '
            f'Load it without re-running benchmarks: {retry}\n',
        )
    else:
        raise interrupt
    return ExitCode.INTERRUPTED


def _print_late_name_error(error: InvalidRunNameError) -> int:
    if error.result_path is None:
        raise error
    print_error(str(error))
    sys.stderr.write(
        f'Result was written to {error.result_path}. '
        'Load it with takt import and another --name.\n',
    )
    return ExitCode.USAGE
