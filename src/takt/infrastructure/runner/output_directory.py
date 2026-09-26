"""Check of the folder that receives the benchmark result file."""

import os
from pathlib import Path

from takt.domain.errors.usage_error import UsageError


def require_output_directory(result_path: Path) -> None:
    """Raise if the result file cannot be created in its folder.

    The runners write the file only after the last benchmark, so a bad
    folder found that late would lose every measured value.

    :param result_path: Absolute path to the result file.
    :raises UsageError: If the folder does not exist or is not writable.
    """
    directory = result_path.parent
    if not directory.is_dir():
        raise _unusable(result_path, 'does not exist')
    if not os.access(directory, os.W_OK | os.X_OK):
        raise _unusable(result_path, 'is not writable')


def _unusable(result_path: Path, reason: str) -> UsageError:
    # Without -o the user never named this folder, so the error names -o.
    return UsageError(
        f'cannot create result file {result_path}: folder '
        f'{result_path.parent} {reason}; choose another file with -o',
    )
