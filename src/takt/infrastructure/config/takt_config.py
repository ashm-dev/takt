"""Settings read from a takt.toml file."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class TaktConfig:
    """Settings read from a ``takt.toml`` file.

    :ivar targets: Target name to database URL, in file order.
    :ivar name_template: Run name template text, or ``None``.
    """

    targets: Mapping[str, str]
    name_template: str | None
