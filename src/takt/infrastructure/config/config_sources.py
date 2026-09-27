"""Raw inputs that takt configuration is resolved from."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class ConfigSources:
    """Raw inputs that takt configuration is resolved from."""

    db_flags: tuple[str, ...]
    """Values of ``--db`` in input order."""

    target_flags: tuple[str, ...]
    """Values of ``--target`` in input order."""

    config_path: Path | None
    """Value of ``--config``, or ``None``."""

    name_flag: str | None
    """Value of ``--name``, or ``None``."""

    environ: Mapping[str, str]
    """Process environment variables."""

    cwd: Path
    """Current working directory."""
