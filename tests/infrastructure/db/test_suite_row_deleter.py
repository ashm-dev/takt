import sqlalchemy as sa

from takt.infrastructure.db.schema.tables import METADATA
from takt.infrastructure.db.suite_row_deleter import delete_suite
from takt.infrastructure.db.suite_row_reader import read_suite
from takt.infrastructure.db.suite_row_writer import insert_suite
from tests.infrastructure.db.suite_factory import make_record


def test_delete_removes_all_rows(engine: sa.Engine) -> None:
    with engine.begin() as connection:
        insert_suite(connection, make_record())
    with engine.begin() as connection:
        delete_suite(connection, 'a' * 64)

    with engine.connect() as connection:
        counts = {
            table.name: connection.execute(
                sa.select(sa.func.count()).select_from(table),
            ).scalar_one()
            for table in METADATA.sorted_tables
        }

    assert len(counts) == 6
    assert set(counts.values()) == {0}


def test_delete_keeps_other_suites(engine: sa.Engine) -> None:
    kept = make_record(suite_hash='b' * 64)
    with engine.begin() as connection:
        insert_suite(connection, make_record())
        insert_suite(connection, kept)
        delete_suite(connection, 'a' * 64)

    with engine.connect() as connection:
        assert read_suite(connection, 'a' * 64) is None
        assert read_suite(connection, 'b' * 64) == kept


def test_delete_missing_hash_is_noop(engine: sa.Engine) -> None:
    with engine.begin() as connection:
        delete_suite(connection, 'c' * 64)
