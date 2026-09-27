"""Compile the takt package with mypyc when ``TAKT_MYPYC=1`` is set."""

import os
import shutil
from pathlib import Path

from mypyc.build import mypycify
from setuptools import Distribution
from setuptools.command.build_ext import build_ext

SOURCE_ROOT = Path('src')
"""Folder that holds the importable ``takt`` package."""

PACKAGE_ROOT = SOURCE_ROOT / 'takt'
"""Folder of the ``takt`` package whose modules mypyc compiles."""

MIGRATIONS_DIR = 'migrations'
"""Folder name of Alembic migrations, which mypyc must skip."""

PARALLEL_JOBS = 2
"""Number of C extensions that are compiled at the same time."""


def collect_sources() -> list[str]:
    """Return every module of the package that mypyc must compile.

    :returns: Sorted paths of ``.py`` files without package initializers
        and without Alembic migrations.
    """
    return sorted(
        str(path)
        for path in PACKAGE_ROOT.rglob('*.py')
        if MIGRATIONS_DIR not in path.parts and path.name != '__init__.py'
    )


def build() -> None:
    """Build mypyc extensions and copy them next to their sources."""
    if os.environ.get('TAKT_MYPYC') != '1':
        return
    extensions = mypycify(collect_sources(), opt_level='3', separate=True)
    distribution = Distribution({'name': 'takt', 'ext_modules': extensions})
    command = build_ext(distribution)
    command.parallel = PARALLEL_JOBS
    command.ensure_finalized()
    command.run()
    for output in command.get_outputs():
        target = SOURCE_ROOT / Path(output).relative_to(command.build_lib)
        shutil.copyfile(output, target)


if __name__ == '__main__':
    build()
