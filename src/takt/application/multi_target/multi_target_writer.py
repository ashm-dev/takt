"""Write one suite to several targets on an all-or-nothing basis."""

import contextlib
from dataclasses import dataclass, field

from takt.application.multi_target.target_outcome import TargetOutcome
from takt.application.multi_target.target_status import TargetStatus
from takt.application.multi_target.write_report import WriteReport
from takt.application.ports.schema_migrator import SchemaMigrator
from takt.application.ports.schema_version_cache import SchemaVersionCache
from takt.application.ports.target_connector import TargetConnector
from takt.application.ports.target_session import TargetSession
from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.target import Target


class MultiTargetWriter:
    """Store a suite in every target or in none of them."""

    def __init__(
        self,
        *,
        connector: TargetConnector,
        migrator: SchemaMigrator,
        cache: SchemaVersionCache,
    ) -> None:
        """Create a writer on top of the storage ports.

        :param connector: Opens sessions to targets.
        :param migrator: Brings target schemas to the latest revision.
        :param cache: Remembers revisions already applied to targets.
        """
        self._connector = connector
        self._migrator = migrator
        self._cache = cache

    def write(
        self,
        record: SuiteRecord,
        targets: tuple[Target, ...],
    ) -> WriteReport:
        """Write the suite to every target or to none of them.

        The write runs in three phases: schema migration of every target,
        insert into every target inside open transactions, and commit
        target by target with compensating deletes when a commit fails.

        :param record: Suite with storage attributes.
        :param targets: Target databases in the order of the report.
        :returns: One outcome per target.
        """
        state = _WriteState(targets=targets)
        if self._migrate(state) and self._insert(state, record):
            self._commit(state, record.suite.hash)
        return state.report()

    def _migrate(self, state: _WriteState) -> bool:
        for index, target in enumerate(state.targets):
            try:
                head, skipped = _prepare_schema(
                    self._migrator,
                    self._cache,
                    target,
                )
            except Exception as error:  # noqa: BLE001 - any target failure must become a status, not a crash
                state.fail(index, error)
                return False
            state.heads.append(head)
            state.skipped.append(skipped)
        return True

    def _insert(self, state: _WriteState, record: SuiteRecord) -> bool:
        for index, target in enumerate(state.targets):
            try:
                self._insert_target(state, index, target, record)
            except Exception as error:  # noqa: BLE001 - any target failure must become a status, not a crash
                state.fail(index, error)
                state.roll_back_open()
                return False
        return True

    def _insert_target(
        self,
        state: _WriteState,
        index: int,
        target: Target,
        record: SuiteRecord,
    ) -> None:
        session = self._connector.open(target)
        try:
            state.load(index, session, record)
        except Exception:
            if not state.skipped[index]:
                raise
            # The cached revision is stale when the database was recreated.
            self._cache.forget(target.url)
            session.rollback()
            session.close()
            state.current = None
            _upgrade(self._migrator, self._cache, target, state.heads[index])
            state.load(index, self._connector.open(target), record)

    def _commit(self, state: _WriteState, suite_hash: str) -> None:
        committed: list[int] = []
        for index in tuple(state.sessions):
            session = state.take(index)
            try:
                session.commit()
            except Exception as error:  # noqa: BLE001 - any target failure must become a status, not a crash
                state.fail(index, error)
                self._compensate(state, committed, suite_hash)
                state.roll_back_open()
                return
            state.current = None
            _close_quietly(session)
            state.mark(index, TargetStatus.WRITTEN)
            committed.append(index)

    def _compensate(
        self,
        state: _WriteState,
        committed: list[int],
        suite_hash: str,
    ) -> None:
        # A committed target cannot roll back, so its suite is deleted.
        for index in committed:
            try:
                _delete_suite(self._connector, state.targets[index], suite_hash)
            except Exception as error:  # noqa: BLE001 - any target failure must become a status, not a crash
                state.fail(index, error, prefix='compensation failed: ')
            else:
                state.mark(index, TargetStatus.ROLLED_BACK)


@dataclass
class _WriteState:
    targets: tuple[Target, ...]
    """Target databases in the order of the report."""

    outcomes: list[TargetOutcome] = field(init=False)
    """Outcome per target, ``not_attempted`` until the target is reached."""

    heads: list[str] = field(default_factory=list)
    """Latest schema revision per target, filled by the migration phase."""

    skipped: list[bool] = field(default_factory=list)
    """Per target, ``True`` when the cached revision skipped the migration."""

    sessions: dict[int, TargetSession] = field(default_factory=dict)
    """Sessions with an inserted, not yet committed suite, by target index."""

    current: TargetSession | None = None
    """Session in use right now, discarded if the target fails."""

    def __post_init__(self) -> None:
        self.outcomes = [
            TargetOutcome(
                target=target,
                status=TargetStatus.NOT_ATTEMPTED,
                existing_name=None,
                error=None,
            )
            for target in self.targets
        ]

    def mark(
        self,
        index: int,
        status: TargetStatus,
        existing_name: str | None = None,
    ) -> None:
        self.outcomes[index] = TargetOutcome(
            target=self.targets[index],
            status=status,
            existing_name=existing_name,
            error=None,
        )

    def fail(self, index: int, error: Exception, prefix: str = '') -> None:
        if self.current is not None:
            _discard(self.current)
            self.current = None
        self.outcomes[index] = TargetOutcome(
            target=self.targets[index],
            status=TargetStatus.FAILED,
            existing_name=None,
            error=prefix + (str(error) or type(error).__name__),
        )

    def load(
        self,
        index: int,
        session: TargetSession,
        record: SuiteRecord,
    ) -> None:
        self.current = session
        loaded, name = session.loaded_name(record.suite.hash)
        if loaded:
            session.rollback()
            self.current = None
            _close_quietly(session)
            self.mark(index, TargetStatus.ALREADY_LOADED, name)
            return
        session.insert(record)
        self.current = None
        self.sessions[index] = session

    def take(self, index: int) -> TargetSession:
        session = self.sessions.pop(index)
        self.current = session
        return session

    def roll_back_open(self) -> None:
        for index, session in self.sessions.items():
            _discard(session)
            self.mark(index, TargetStatus.ROLLED_BACK)
        self.sessions.clear()

    def report(self) -> WriteReport:
        return WriteReport(outcomes=tuple(self.outcomes))


def _prepare_schema(
    migrator: SchemaMigrator,
    cache: SchemaVersionCache,
    target: Target,
) -> tuple[str, bool]:
    head = migrator.head(target)
    if cache.get(target.url) == head:
        return head, True
    _upgrade(migrator, cache, target, head)
    return head, False


def _upgrade(
    migrator: SchemaMigrator,
    cache: SchemaVersionCache,
    target: Target,
    head: str,
) -> None:
    migrator.upgrade(target)
    cache.put(target.url, head)


def _delete_suite(
    connector: TargetConnector,
    target: Target,
    suite_hash: str,
) -> None:
    session = connector.open(target)
    with contextlib.ExitStack() as cleanup:
        cleanup.callback(_close_quietly, session)
        session.delete(suite_hash)
        session.commit()


def _discard(session: TargetSession) -> None:
    with contextlib.suppress(Exception):
        session.rollback()
    _close_quietly(session)


def _close_quietly(session: TargetSession) -> None:
    with contextlib.suppress(Exception):
        session.close()
