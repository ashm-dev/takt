from collections.abc import Sequence
from dataclasses import dataclass, field

from takt.domain.model.suite_record import SuiteRecord
from takt.domain.model.suite_summary import SuiteSummary
from takt.domain.model.target import Target

DEFAULT_HEAD = '0001'


@dataclass
class FakeWorld:
    journal: list[str] = field(default_factory=list)
    loaded: dict[str, str | None] = field(default_factory=dict)
    stored: set[str] = field(default_factory=set)
    fail: dict[str, int] = field(default_factory=dict)
    heads: dict[str, str] = field(default_factory=dict)
    cache: dict[str, str] = field(default_factory=dict)
    inserted: list[SuiteRecord] = field(default_factory=list)
    empty_errors: set[str] = field(default_factory=set)

    def call(self, operation: str, name: str) -> None:
        key = f'{operation}:{name}'
        self.journal.append(key)
        if key in self.empty_errors:
            raise RuntimeError
        if self.fail.get(key, 0) > 0:
            self.fail[key] -= 1
            msg = f'{operation} failed on {name}'
            raise RuntimeError(msg)


def target_name(url: str) -> str:
    return url.removeprefix('sqlite:///').removesuffix('.db')


def assert_subsequence(journal: Sequence[str], expected: Sequence[str]) -> None:
    remaining = iter(journal)
    missing = [entry for entry in expected if entry not in remaining]
    assert not missing, f'{missing} not found in order in {journal}'


class FakeSession:
    def __init__(self, world: FakeWorld, target: Target) -> None:
        self.world = world
        self.name = target.display()
        self.pending = False

    def loaded_name(self, _suite_hash: str) -> tuple[bool, str | None]:
        self.world.call('loaded', self.name)
        name = self.world.loaded.get(self.name)
        return (self.name in self.world.loaded, name)

    def insert(self, record: SuiteRecord) -> None:
        self.world.call('insert', self.name)
        self.world.inserted.append(record)
        self.pending = True

    def delete(self, _suite_hash: str) -> None:
        self.world.call('delete', self.name)
        self.world.stored.discard(self.name)

    def get(self, suite_hash: str) -> SuiteRecord:
        raise NotImplementedError

    def find_by_name(self, name: str) -> tuple[SuiteSummary, ...]:
        raise NotImplementedError

    def find_by_hash_prefix(
        self,
        prefix: str,
        name: str | None,
    ) -> tuple[SuiteSummary, ...]:
        raise NotImplementedError

    def commit(self) -> None:
        self.world.call('commit', self.name)
        if self.pending:
            self.world.stored.add(self.name)
        self.pending = False

    def rollback(self) -> None:
        self.world.call('rollback', self.name)
        self.pending = False

    def close(self) -> None:
        self.world.call('close', self.name)


class FakeConnector:
    def __init__(self, world: FakeWorld) -> None:
        self.world = world

    def open(self, target: Target) -> FakeSession:
        self.world.call('open', target.display())
        return FakeSession(self.world, target)


class FakeMigrator:
    def __init__(self, world: FakeWorld) -> None:
        self.world = world

    def head(self, target: Target) -> str:
        name = target.display()
        self.world.call('head', name)
        return self.world.heads.get(name, DEFAULT_HEAD)

    def upgrade(self, target: Target) -> None:
        self.world.call('upgrade', target.display())


class FakeCache:
    def __init__(self, world: FakeWorld) -> None:
        self.world = world

    def get(self, url: str) -> str | None:
        self.world.call('get', target_name(url))
        return self.world.cache.get(url)

    def put(self, url: str, revision: str) -> None:
        self.world.call('put', target_name(url))
        self.world.cache[url] = revision

    def forget(self, url: str) -> None:
        self.world.call('forget', target_name(url))
        self.world.cache.pop(url, None)
