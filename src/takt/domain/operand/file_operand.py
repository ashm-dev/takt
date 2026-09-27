"""Compare operand that names an existing file."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class FileOperand:
    """Compare operand that names an existing file."""

    text: str
    """Operand text as the user wrote it."""

    path: Path
    """Expanded filesystem path to the result file."""
