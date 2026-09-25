from takt.application.multi_target.multi_target_writer import MultiTargetWriter
from takt.application.multi_target.target_status import TargetStatus
from takt.application.multi_target.write_report import WriteReport
from takt.domain.model.target import Target
from tests.application.multi_target.fakes import (
    FakeCache,
    FakeConnector,
    FakeMigrator,
    FakeWorld,
    assert_subsequence,
)
from tests.infrastructure.db.suite_factory import make_record

WR = TargetStatus.WRITTEN
AL = TargetStatus.ALREADY_LOADED
FL = TargetStatus.FAILED
RB = TargetStatus.ROLLED_BACK
NA = TargetStatus.NOT_ATTEMPTED
HEAD = '0001'
TARGETS = tuple(
    Target(name=name, url=f'sqlite:///{name}.db', dialect='sqlite')
    for name in ('a', 'b', 'c')
)


def url(name: str) -> str:
    return f'sqlite:///{name}.db'


def write(
    world: FakeWorld,
    targets: tuple[Target, ...] = TARGETS,
) -> WriteReport:
    writer = MultiTargetWriter(
        connector=FakeConnector(world),
        migrator=FakeMigrator(world),
        cache=FakeCache(world),
    )
    return writer.write(make_record(), targets)


def write_expecting(
    world: FakeWorld,
    expected: tuple[TargetStatus, ...],
) -> WriteReport:
    report = write(world)
    assert tuple(outcome.status for outcome in report.outcomes) == expected
    return report


def journal_has(world: FakeWorld, *prefixes: str) -> bool:
    return any(entry.startswith(prefixes) for entry in world.journal)


def warm_cache(*names: str) -> dict[str, str]:
    return {url(name): HEAD for name in names}


def test_all_targets_written() -> None:
    world = FakeWorld()

    report = write_expecting(world, (WR, WR, WR))

    assert world.stored == {'a', 'b', 'c'}
    assert world.cache == warm_cache('a', 'b', 'c')
    assert report.succeeded
    assert [outcome.target for outcome in report.outcomes] == list(TARGETS)


def test_cache_hit_skips_upgrade() -> None:
    world = FakeWorld(cache=warm_cache('a', 'b', 'c'))

    write_expecting(world, (WR, WR, WR))

    assert not journal_has(world, 'upgrade:')


def test_stale_cache_retried_once() -> None:
    world = FakeWorld(cache=warm_cache('b'), fail={'insert:b': 1})

    write_expecting(world, (WR, WR, WR))

    assert_subsequence(
        world.journal,
        [
            'insert:b',
            'forget:b',
            'rollback:b',
            'close:b',
            'upgrade:b',
            'put:b',
            'open:b',
            'loaded:b',
            'insert:b',
        ],
    )
    assert world.stored == {'a', 'b', 'c'}


def test_stale_cache_retried_when_loaded_name_fails() -> None:
    world = FakeWorld(cache=warm_cache('b'), fail={'loaded:b': 1})

    write_expecting(world, (WR, WR, WR))

    assert_subsequence(
        world.journal,
        [
            'loaded:b',
            'forget:b',
            'upgrade:b',
            'put:b',
            'open:b',
            'loaded:b',
            'insert:b',
        ],
    )


def test_second_insert_failure_after_retry_fails() -> None:
    world = FakeWorld(cache=warm_cache('b'), fail={'insert:b': 2})

    report = write_expecting(world, (RB, FL, NA))

    assert report.outcomes[1].error == 'insert failed on b'
    assert world.stored == set()
    assert 'open:c' not in world.journal
    assert not report.succeeded


def test_insert_failure_without_cache_is_not_retried() -> None:
    world = FakeWorld(fail={'insert:b': 1})

    write_expecting(world, (RB, FL, NA))

    assert world.journal.count('upgrade:b') == 1
    assert_subsequence(world.journal, ['insert:b', 'rollback:b', 'close:b'])


def test_migration_failure_stops_before_any_write() -> None:
    world = FakeWorld(fail={'upgrade:b': 1})

    report = write_expecting(world, (NA, FL, NA))

    assert report.outcomes[1].error == 'upgrade failed on b'
    assert not journal_has(world, 'open:')


def test_already_loaded_target_is_skipped() -> None:
    world = FakeWorld(loaded={'b': 'old'})

    report = write_expecting(world, (WR, AL, WR))

    assert report.outcomes[1].existing_name == 'old'
    assert 'insert:b' not in world.journal
    assert_subsequence(world.journal, ['loaded:b', 'rollback:b', 'close:b'])
    assert report.succeeded


def test_all_already_loaded() -> None:
    world = FakeWorld(loaded=dict.fromkeys(('a', 'b', 'c')))

    report = write_expecting(world, (AL, AL, AL))

    assert not journal_has(world, 'insert:', 'commit:')
    assert report.succeeded


def test_commit_failure_compensates_committed() -> None:
    world = FakeWorld(fail={'commit:c': 1})

    write_expecting(world, (RB, RB, FL))

    assert_subsequence(world.journal, ['commit:c', 'delete:a', 'delete:b'])
    assert world.stored == set()


def test_commit_failure_in_middle_rolls_back_rest() -> None:
    world = FakeWorld(fail={'commit:b': 1})

    write_expecting(world, (RB, FL, RB))

    assert 'delete:a' in world.journal
    assert 'commit:c' not in world.journal
    assert 'rollback:c' in world.journal
    assert world.stored == set()


def test_compensation_failure_is_reported() -> None:
    world = FakeWorld(fail={'commit:c': 1, 'delete:a': 1})

    report = write_expecting(world, (FL, RB, FL))

    assert report.outcomes[0].error == (
        'compensation failed: delete failed on a'
    )
    assert 'a' in world.stored
    assert 'b' not in world.stored


def test_open_failure_rolls_back_previous() -> None:
    world = FakeWorld(fail={'open:b': 1})

    write_expecting(world, (RB, FL, NA))

    assert 'rollback:a' in world.journal


def test_loaded_name_failure_is_target_failure() -> None:
    world = FakeWorld(fail={'loaded:a': 1})

    write_expecting(world, (FL, NA, NA))

    assert not journal_has(world, 'insert:')


def test_already_loaded_kept_on_later_failure() -> None:
    world = FakeWorld(loaded={'a': 'x'}, fail={'insert:c': 1})

    report = write_expecting(world, (AL, RB, FL))

    assert report.outcomes[0].existing_name == 'x'


def test_empty_targets_returns_empty_report() -> None:
    world = FakeWorld()

    report = write(world, ())

    assert report.outcomes == ()
    assert report.succeeded
    assert world.journal == []


def test_empty_exception_text_uses_class_name() -> None:
    world = FakeWorld(empty_errors={'insert:a'})

    report = write_expecting(world, (FL, NA, NA))

    assert report.outcomes[0].error == 'RuntimeError'
