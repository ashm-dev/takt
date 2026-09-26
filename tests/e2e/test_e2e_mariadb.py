import os
import shlex
from pathlib import Path

import pytest
import sqlalchemy as sa

from takt.cli.main import main
from takt.domain.model.target import Target
from takt.infrastructure.cache.file_schema_version_cache import (
    FileSchemaVersionCache,
)
from tests.e2e.conftest import CountSuites, MakeResult

pytestmark = pytest.mark.mariadb

NOMINAL = (0.1, 0.11, 0.1)
SLOWER = (0.2, 0.21, 0.2)
CLOSED_PORT_URL = 'mariadb+pymysql://takt:takt@127.0.0.1:1/takt'
SCRIPT_FLAGS = (
    '--processes',
    '1',
    '--values',
    '3',
    '--warmups',
    '1',
    '--loops',
    '1',
)


def drop_takt_tables(url: str) -> None:
    engine = sa.create_engine(url, poolclass=sa.pool.NullPool)
    metadata = sa.MetaData()
    metadata.reflect(
        engine,
        only=lambda table_name, _: table_name.startswith('takt_'),
    )
    with engine.begin() as connection:
        for table in reversed(metadata.sorted_tables):
            connection.execute(sa.schema.DropTable(table))
    engine.dispose()


def test_import_to_sqlite_and_mariadb(
    make_result: MakeResult,
    sqlite_url: str,
    mariadb_target: Target,
    count_suites: CountSuites,
    capsys: pytest.CaptureFixture[str],
) -> None:
    make_result('a.json', 'nbody', NOMINAL)

    code = main(
        ['import', 'a.json', '--db', sqlite_url, '--db', mariadb_target.url],
    )

    assert code == 0
    assert capsys.readouterr().out.count(': written') == 2
    assert count_suites(sqlite_url) == 1
    assert count_suites(mariadb_target.url) == 1


def test_one_target_down_writes_nothing(
    make_result: MakeResult,
    sqlite_url: str,
    count_suites: CountSuites,
    capsys: pytest.CaptureFixture[str],
) -> None:
    make_result('a.json', 'nbody', NOMINAL)

    code = main(
        ['import', 'a.json', '--db', sqlite_url, '--db', CLOSED_PORT_URL],
    )

    captured = capsys.readouterr()
    assert code == 1
    maria_lines = [
        line for line in captured.out.splitlines() if '127.0.0.1:1' in line
    ]
    assert len(maria_lines) == 1
    assert 'failed:' in maria_lines[0]
    assert 'error: result was not written to all targets' in captured.err
    assert count_suites(sqlite_url) == 0


def test_run_failure_prints_retry(
    bench_script: Path,
    sqlite_url: str,
    mariadb_target: Target,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code = main(
        [
            'run',
            str(bench_script),
            *SCRIPT_FLAGS,
            '--db',
            sqlite_url,
            '--db',
            CLOSED_PORT_URL,
        ],
    )

    err = capsys.readouterr().err
    result_files = list(tmp_path.glob('takt-*.json'))
    assert code == 1
    assert 'Retry without re-running benchmarks: takt import ' in err
    assert len(result_files) == 1
    assert shlex.join(('--db', sqlite_url, '--db', CLOSED_PORT_URL)) in err
    assert result_files[0].name in err
    assert (
        main(
            [
                'import',
                str(result_files[0]),
                '--db',
                sqlite_url,
                '--db',
                mariadb_target.url,
            ],
        )
        == 0
    )


def test_compare_from_mariadb(
    make_result: MakeResult,
    mariadb_target: Target,
) -> None:
    make_result('a.json', 'nbody', NOMINAL)
    make_result('b.json', 'nbody', SLOWER)
    main(['import', 'a.json', '--db', mariadb_target.url, '--name', 'base'])

    code = main(['compare', 'base', 'b.json', '--db', mariadb_target.url])

    assert code == 0


def test_schema_cache_recovers_after_drop(
    make_result: MakeResult,
    mariadb_target: Target,
    count_suites: CountSuites,
) -> None:
    make_result('a.json', 'nbody', NOMINAL)
    make_result('b.json', 'nbody', SLOWER)
    assert main(['import', 'a.json', '--db', mariadb_target.url]) == 0
    cache = FileSchemaVersionCache.default(os.environ)
    assert cache.get(mariadb_target.url) is not None
    drop_takt_tables(mariadb_target.url)

    code = main(['import', 'b.json', '--db', mariadb_target.url])

    assert code == 0
    assert count_suites(mariadb_target.url) == 1
