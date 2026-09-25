"""Compare operand that names an existing file."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class FileOperand:
    """Compare operand that names an existing file.

    :ivar text: Operand text as the user wrote it.
    :ivar path: Expanded filesystem path to the result file.
    """

    text: str
    path: Path
