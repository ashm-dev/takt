"""Raw inputs that takt configuration is resolved from."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class ConfigSources:
    """Raw inputs that takt configuration is resolved from.

    :ivar db_flags: Values of ``--db`` in input order.
    :ivar target_flags: Values of ``--target`` in input order.
    :ivar config_path: Value of ``--config``, or ``None``.
    :ivar name_flag: Value of ``--name``, or ``None``.
    :ivar environ: Process environment variables.
    :ivar cwd: Current working directory.
    """

    db_flags: tuple[str, ...]
    target_flags: tuple[str, ...]
    config_path: Path | None
    name_flag: str | None
    environ: Mapping[str, str]
    cwd: Path
