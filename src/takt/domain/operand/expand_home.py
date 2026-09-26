"""Expansion of ``~`` in a path that the user wrote."""

from pathlib import Path


def expand_home(text: str) -> Path:
    """Expand a leading ``~`` or ``~name`` like a shell does.

    :param text: Path as the user wrote it.
    :returns: The expanded path, or the path as written when user
        ``name`` does not exist (a shell keeps it too) or contains a
        NUL byte.
    """
    path = Path(text)
    try:
        return path.expanduser()
    except RuntimeError, ValueError:
        return path
