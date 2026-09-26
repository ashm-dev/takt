"""Command that retries a failed write without re-running benchmarks."""

import argparse
import shlex
from pathlib import Path

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
