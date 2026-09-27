import dataclasses
import operator
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

from takt.domain.errors.invalid_result_error import InvalidResultError
from takt.domain.model.suite import Suite
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.suite_source import SuiteSource
from takt.domain.model.suite_summary import SuiteSummary
from takt.domain.model.target import Target
from tests.application.use_cases.fakes import make_suite

HASH_A = '3fa2b1'.ljust(64, '0')
"""Suite hash that shares the ``3fa2b`` prefix with ``HASH_C``."""

HASH_B = '9c01de'.ljust(64, '0')
"""Suite hash with a prefix that no other test hash has."""

HASH_C = '3fa2b2'.ljust(64, '0')
"""Suite hash that shares the ``3fa2b`` prefix with ``HASH_A``."""

LOADED_AT = datetime(2026, 9, 25, tzinfo=UTC)
"""Load time given to every record built by ``record``."""


def suite(suite_hash: str, result_date: datetime | None = None) -> Suite:
    return dataclasses.replace(
        make_suite(),
        hash=suite_hash,
        result_date=result_date,
    )


def record(
    suite_hash: str,
    name: str | None,
    result_date: datetime | None = None,
) -> SuiteRecord:
    return SuiteRecord(
        suite=suite(suite_hash, result_date),
        name=name,
        source=SuiteSource.IMPORT,
        loaded_at=LOADED_AT,
    )


class FakeReader:
    def __init__(self, suites: Mapping[Path, Suite]) -> None:
        self.suites = suites

    def read(self, path: Path) -> Suite:
        if path not in self.suites:
            msg = f'unknown result file {path}'
            raise InvalidResultError(msg)
        return self.suites[path]


class FakeSession:
    def __init__(self, records: Iterable[SuiteRecord] = ()) -> None:
        self.records = list(records)
        self.calls: list[str] = []
        self.prefix_lookups: list[tuple[str, str | None]] = []
        self.rollback_error: Exception | None = None

    def loaded_name(self, suite_hash: str) -> tuple[bool, str | None]:
        raise NotImplementedError

    def insert(self, record: SuiteRecord) -> None:
        raise NotImplementedError

    def delete(self, suite_hash: str) -> None:
        raise NotImplementedError

    def get(self, suite_hash: str) -> SuiteRecord:
        return next(
            stored for stored in self.records if stored.suite.hash == suite_hash
        )

    def find_by_name(self, name: str) -> tuple[SuiteSummary, ...]:
        return _summaries(
            stored for stored in self.records if stored.name == name
        )

    def find_by_hash_prefix(
        self,
        prefix: str,
        name: str | None,
    ) -> tuple[SuiteSummary, ...]:
        self.prefix_lookups.append((prefix, name))
        return _summaries(
            stored
            for stored in self.records
            if stored.suite.hash.startswith(prefix)
            and (name is None or stored.name == name)
        )

    def commit(self) -> None:
        self.calls.append('commit')

    def rollback(self) -> None:
        self.calls.append('rollback')
        if self.rollback_error is not None:
            raise self.rollback_error

    def close(self) -> None:
        self.calls.append('close')


class FakeConnector:
    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.opened: list[Target] = []

    def open(self, target: Target) -> FakeSession:
        self.opened.append(target)
        return self.session


def _summaries(records: Iterable[SuiteRecord]) -> tuple[SuiteSummary, ...]:
    summaries = [
        SuiteSummary(
            hash=stored.suite.hash,
            name=stored.name,
            result_date=stored.suite.result_date,
        )
        for stored in records
    ]
    summaries.sort(key=operator.attrgetter('hash'))
    dated = [
        summary for summary in summaries if summary.result_date is not None
    ]
    dated.sort(key=operator.attrgetter('result_date'))
    undated = [summary for summary in summaries if summary.result_date is None]
    return (*dated, *undated)
