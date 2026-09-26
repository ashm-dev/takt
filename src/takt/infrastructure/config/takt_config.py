"""Settings read from a takt.toml file."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class TaktConfig:
    """Settings read from a ``takt.toml`` file.

    :ivar targets: Target name to database URL, in file order.
    :ivar name_template: Run name template text, or ``None``.
    :ivar path: File the settings were read from, or ``None`` when there
        was no file.
    """

    targets: Mapping[str, str]
    name_template: str | None
    path: Path | None
