"""Command that retries a failed write without re-running benchmarks."""

import argparse
import shlex
from pathlib import Path


def build_retry_command(args: argparse.Namespace, result_path: Path) -> str:
    """Build ``takt import`` with the same target and name flags.

    :param args: Parsed arguments of ``takt run``.
    :param result_path: Result file left on disk by the run.
    :returns: Shell-quoted command line.
    """
    words = ['takt', 'import', str(result_path)]
    for url in args.db:
        words.extend(('--db', url))
    for target in args.target:
        words.extend(('--target', target))
    if args.config is not None:
        words.extend(('--config', str(args.config)))
    if args.name is not None:
        words.extend(('--name', args.name))
    return shlex.join(words)
