"""Own flags of takt that are never passed to the runner."""

from typing import Final

DB_FLAG: Final = '--db'
TARGET_FLAG: Final = '--target'
CONFIG_FLAG: Final = '--config'
NAME_FLAG: Final = '--name'
TAKT_FLAGS: Final = (DB_FLAG, TARGET_FLAG, CONFIG_FLAG, NAME_FLAG)
