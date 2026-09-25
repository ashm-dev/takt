"""Own flags of takt that are never passed to the runner."""

from typing import Final

TAKT_FLAGS: Final[tuple[str, ...]] = ('--db', '--target', '--config', '--name')
