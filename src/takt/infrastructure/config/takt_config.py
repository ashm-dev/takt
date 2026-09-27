"""Settings read from a takt.toml file."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class TaktConfig:
    """Settings read from a ``takt.toml`` file."""

    targets: Mapping[str, str]
    """Target name to database URL, in file order."""

    name_template: str | None
    """Run name template text, or ``None``."""

    path: Path | None
    """File the settings were read from, or ``None`` when there was no file."""
