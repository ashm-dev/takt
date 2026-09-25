"""Alias for any parsed compare operand."""

from typing import TypeAlias

from takt.domain.operand.file_operand import FileOperand
from takt.domain.operand.plain_operand import PlainOperand
from takt.domain.operand.tagged_operand import TaggedOperand

Operand: TypeAlias = FileOperand | PlainOperand | TaggedOperand
