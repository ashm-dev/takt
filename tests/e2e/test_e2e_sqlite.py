import gzip
from pathlib import Path

import pytest
import sqlalchemy as sa

from takt.cli.main import main
from tests.e2e.conftest import CountSuites, MakeResult

NOMINAL = (0.1, 0.11, 0.1)
SLOWER = (0.2, 0.21, 0.2)


@pytest.fixture
def result_a(make_result: MakeResult) -> Path:
    return make_result('a.json', 'nbody', NOMINAL)


def write_toml(path: Path, targets: dict[str, Path]) -> None:
    sections = [
        f'[targets.{name}]\nurl = "sqlite:///{database}"\n'
        for name, database in targets.items()
    ]
    path.write_text('\n'.join(sections), encoding='utf-8')


def test_run_pyperf_script(
    bench_script: Path,
    sqlite_url: str,
    count_suites: CountSuites,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code = main(
        [
            'run',
            str(bench_script),
            '--processes',
            '1',
            '--values',
            '3',
            '--warmups',
            '1',
            '--loops',
            '1',
            '--db',
            sqlite_url,
            '--name',
            'script {date}',
        ],
    )

    assert code == 0
    assert ': written' in capsys.readouterr().out
    assert len(list(tmp_path.glob('takt-*.json'))) == 1
    assert count_suites(sqlite_url) == 1


@pytest.mark.usefixtures('result_a')
def test_import_twice(
    sqlite_url: str,
    count_suites: CountSuites,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = main(['import', 'a.json', '--db', sqlite_url, '--name', 'base'])
    first_out = capsys.readouterr().out
    second = main(['import', 'a.json', '--db', sqlite_url, '--name', 'other'])

    assert first == 0
    assert ': written' in first_out
    assert second == 0
    assert "already loaded as 'base'" in capsys.readouterr().out
    assert count_suites(sqlite_url) == 1


def test_import_gz_same_hash(
    result_a: Path,
    sqlite_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with gzip.open('a.json.gz', 'wt', encoding='utf-8') as compressed:
        compressed.write(result_a.read_text(encoding='utf-8'))
    main(['import', 'a.json', '--db', sqlite_url, '--name', 'base'])
    capsys.readouterr()

    code = main(['import', 'a.json.gz', '--db', sqlite_url])

    assert code == 0
    assert 'already loaded' in capsys.readouterr().out


@pytest.mark.usefixtures('result_a')
def test_import_to_two_sqlite_targets_via_toml(
    count_suites: CountSuites,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    one = tmp_path / 'one.db'
    two = tmp_path / 'two.db'
    write_toml(tmp_path / 'takt.toml', {'one': one, 'two': two})

    code = main(['import', 'a.json'])

    assert code == 0
    assert count_suites(f'sqlite:///{one}') == 1
    assert count_suites(f'sqlite:///{two}') == 1
    capsys.readouterr()
    assert main(['import', 'a.json', '--target', 'one']) == 0
    assert 'already loaded' in capsys.readouterr().out


@pytest.mark.usefixtures('result_a')
def test_env_overrides_toml(
    count_suites: CountSuites,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    one = tmp_path / 'one.db'
    write_toml(tmp_path / 'takt.toml', {'one': one})
    env_database = tmp_path / 'env.db'
    env_url = f'sqlite:///{env_database}'
    monkeypatch.setenv('TAKT_DB', env_url)

    code = main(['import', 'a.json'])

    assert code == 0
    assert count_suites(env_url) == 1
    engine = sa.create_engine(f'sqlite:///{one}', poolclass=sa.pool.NullPool)
    assert sa.inspect(engine).get_table_names() == []
    engine.dispose()


@pytest.mark.usefixtures('result_a')
def test_compare_file_and_db(
    make_result: MakeResult,
    sqlite_url: str,
    tmp_path: Path,
) -> None:
    make_result('b.json', 'nbody', SLOWER)
    main(['import', 'a.json', '--db', sqlite_url, '--name', 'base'])

    code = main(
        [
            'compare',
            'base',
            'b.json',
            '--db',
            sqlite_url,
            '--markdown',
            'out.md',
        ],
    )

    assert code == 0
    lines = (tmp_path / 'out.md').read_text(encoding='utf-8').splitlines()
    assert 'Benchmark' in lines[0]
    assert 'base' in lines[0]
    assert 'b.json' in lines[0]
    nbody = [line for line in lines if line.startswith('| nbody')]
    assert len(nbody) == 1
    assert 'slower' in nbody[0]


@pytest.mark.usefixtures('result_a')
def test_compare_name_index(
    make_result: MakeResult,
    sqlite_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    make_result('b.json', 'nbody', SLOWER)
    make_result('c.json', 'nbody', (0.3, 0.31, 0.3))
    main(['import', 'a.json', '--db', sqlite_url, '--name', 'nightly'])
    main(['import', 'c.json', '--db', sqlite_url, '--name', 'nightly'])
    capsys.readouterr()

    ambiguous = main(['compare', 'nightly', 'b.json', '--db', sqlite_url])
    err = capsys.readouterr().err

    assert ambiguous == 1
    assert 'is ambiguous' in err
    assert 'nightly:0' in err
    assert 'nightly:1' in err
    assert main(['compare', 'nightly:0', 'nightly:1', '--db', sqlite_url]) == 0


@pytest.mark.usefixtures('result_a')
def test_compare_files_without_db(make_result: MakeResult) -> None:
    make_result('b.json', 'nbody', SLOWER)

    assert main(['compare', 'a.json', 'b.json']) == 0


@pytest.mark.usefixtures('result_a')
def test_compare_unknown_operand(
    sqlite_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(['import', 'a.json', '--db', sqlite_url])
    capsys.readouterr()

    code = main(['compare', 'a.json', 'missing', '--db', sqlite_url])

    assert code == 1
    assert capsys.readouterr().err == (
        "error: operand 'missing' not found: "
        'no file, run name or hash prefix matches\n'
    )


@pytest.mark.usefixtures('result_a')
def test_compare_empty_database(
    sqlite_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(['compare', 'a.json', 'base', '--db', sqlite_url])

    assert code == 1
    engine_url = sqlite_url.replace('sqlite:', 'sqlite+pysqlite:', 1)
    assert capsys.readouterr().err == (
        f'error: cannot read from database {engine_url}: '
        'no such table: takt_suite\n'
    )


@pytest.mark.usefixtures('result_a')
def test_compare_unreachable_database(
    capsys: pytest.CaptureFixture[str],
) -> None:
    url = 'mariadb+pymysql://u:secret@127.0.0.1:1/x'

    code = main(['compare', 'a.json', 'base', '--db', url])

    assert code == 1
    err = capsys.readouterr().err
    assert err.startswith(
        'error: cannot connect to database '
        'mariadb+pymysql://u:***@127.0.0.1:1/x: ',
    )
    assert err.count('\n') == 1
    assert 'secret' not in err


@pytest.mark.usefixtures('result_a')
def test_import_without_targets(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(['import', 'a.json'])

    assert code == 2
    assert capsys.readouterr().err == (
        'error: no database targets configured: '
        'use --db, --target, TAKT_DB or takt.toml\n'
    )


@pytest.mark.usefixtures('result_a')
def test_name_with_colon_rejected(
    sqlite_url: str,
    count_suites: CountSuites,
) -> None:
    code = main(['import', 'a.json', '--db', sqlite_url, '--name', 'a:b'])

    assert code == 2
    assert count_suites(sqlite_url) == 0


@pytest.mark.usefixtures('result_a')
def test_unsupported_dialect(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code = main(
        ['import', 'a.json', '--db', 'postgresql://u:p@localhost/db'],
    )

    assert code == 2
    assert 'error:' in capsys.readouterr().err
    assert not (tmp_path / 'takt.db').exists()
