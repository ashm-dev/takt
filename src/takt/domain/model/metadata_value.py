"""Type of a pyperf metadata value."""

from typing import TypeAlias

MetadataValue: TypeAlias = int | float | str | tuple[str, ...]
"""Any value that a pyperf metadata key can hold."""
