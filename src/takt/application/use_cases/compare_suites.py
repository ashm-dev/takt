"""Compare benchmark suites from files and database runs."""

import contextlib
from pathlib import Path

from takt.application.ports.result_reader import ResultReader
from takt.application.ports.target_connector import TargetConnector
from takt.application.use_cases.compare_request import CompareRequest
from takt.application.use_cases.operand_resolver import OperandResolver
from takt.domain.compare.build_compare_table import build_compare_table
from takt.domain.compare.compare_table import CompareTable
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.operand.file_operand import FileOperand
from takt.domain.operand.operand import Operand
from takt.domain.operand.parse_operand import parse_operand

_MIN_OPERANDS = 2
"""Smallest operand count: the base and at least one run to compare with it."""


class CompareSuites:
    """Build the compare table for result files and stored runs."""

    def __init__(
        self,
        *,
        reader: ResultReader,
        connector: TargetConnector,
    ) -> None:
        """Create the use case on top of its ports.

        :param reader: Reads result files.
        :param connector: Opens the database with stored runs.
        """
        self._reader = reader
        self._connector = connector

    def execute(self, request: CompareRequest) -> CompareTable:
        """Resolve every operand and compare the rest against the first.

        :param request: Operands and the optional database target.
        :returns: The compare table.
        :raises ConfigurationError: If there are fewer than two operands,
            or a database operand is given without a target or with an
            invalid database setting.
        :raises OperandNotFoundError: If an operand is empty or malformed,
            or matches nothing.
        :raises AmbiguousOperandError: If an operand matches several runs.
        :raises InvalidResultError: If a result file cannot be read.
        :raises NoCommonBenchmarksError: If the suites share no benchmark.
        :raises ExecutionError: If the database cannot be connected to or
            read.
        """
        if len(request.operands) < _MIN_OPERANDS:
            msg = 'compare needs at least two operands'
            raise ConfigurationError(msg)
        operands = [
            parse_operand(operand, Path.is_file) for operand in request.operands
        ]
        with contextlib.ExitStack() as cleanup:
            resolver = self._resolver(operands, request, cleanup)
            labeled = [resolver.resolve(operand) for operand in operands]
        return build_compare_table(labeled[0], labeled[1:])

    def _resolver(
        self,
        operands: list[Operand],
        request: CompareRequest,
        cleanup: contextlib.ExitStack,
    ) -> OperandResolver:
        stored = [
            operand.text
            for operand in operands
            if not isinstance(operand, FileOperand)
        ]
        if not stored:
            return OperandResolver(
                reader=self._reader,
                session=None,
                target_label=None,
            )
        target = request.find_target()
        if target is None:
            msg = (
                f"operand '{stored[0]}' is not a file "
                'and no database target is configured'
            )
            raise ConfigurationError(msg)
        session = self._connector.open(target)
        # Callbacks run in reverse order, so rollback precedes close.
        cleanup.callback(session.close)
        cleanup.callback(session.rollback)
        return OperandResolver(
            reader=self._reader,
            session=session,
            target_label=target.display(),
        )
