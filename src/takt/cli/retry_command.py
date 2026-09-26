"""Command that retries a failed write without re-running benchmarks."""

import argparse
import shlex
from pathlib import Path

from takt.domain.naming.literal_template import literal_template
from takt.infrastructure.runner.takt_flags import (
    CONFIG_FLAG,
    DB_FLAG,
    NAME_FLAG,
    TARGET_FLAG,
)


def build_retry_command(
    args: argparse.Namespace,
    result_path: Path,
    name: str | None,
) -> str:
    """Build ``takt import`` with the same target flags and the given name.

    :param args: Parsed arguments of ``takt run``.
    :param result_path: Result file left on disk by the run.
    :param name: Value of ``--name``, or ``None`` to leave the flag out.
    :returns: Shell-quoted command line.
    """
    words = ['takt', 'import', str(result_path)]
    for url in args.db:
        words.extend((DB_FLAG, url))
    for target in args.target:
        words.extend((TARGET_FLAG, target))
    if args.config is not None:
        words.extend((CONFIG_FLAG, str(args.config)))
    if name is not None:
        words.extend((NAME_FLAG, name))
    return shlex.join(words)


def build_retry_command_for_name(
    args: argparse.Namespace,
    result_path: Path,
    name: str | None,
) -> str:
    """Build ``takt import`` that stores the result under a final run name.

    :param args: Parsed arguments of ``takt run``.
    :param result_path: Result file left on disk by the run.
    :param name: Run name the run gave the result, or ``None``.
    :returns: Shell-quoted command line.
    """
    # A template with {date} would give the retried result another name.
    template = None if name is None else literal_template(name)
    return build_retry_command(args, result_path, template)
