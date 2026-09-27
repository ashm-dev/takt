"""Own flags of takt that are never passed to the runner."""

from typing import Final

DB_FLAG: Final = '--db'
"""Flag with a database URL to store results in."""

TARGET_FLAG: Final = '--target'
"""Flag with a target name from ``takt.toml``."""

CONFIG_FLAG: Final = '--config'
"""Flag with the path to a config file."""

NAME_FLAG: Final = '--name'
"""Flag with the run name template."""

TAKT_FLAGS: Final = (DB_FLAG, TARGET_FLAG, CONFIG_FLAG, NAME_FLAG)
"""Flags that takt takes out before it calls the runner."""
