from collections.abc import Callable, Sequence
from pathlib import Path

import pyperf
import pytest
import sqlalchemy as sa

BENCH_SCRIPT = """import time

import pyperf

runner = pyperf.Runner()
runner.bench_func("sleep_small", time.sleep, 0.0001)
"""

MakeResult = Callable[[Path | str, str, Sequence[float]], Path]
CountSuites = Callable[[str], int]


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    monkeypatch.delenv('TAKT_DB', raising=False)
    monkeypatch.delenv('TAKT_NAME', raising=False)


@pytest.fixture
def bench_script(tmp_path: Path) -> Path:
    script = tmp_path / 'bench_sleep.py'
    script.write_text(BENCH_SCRIPT, encoding='utf-8')
    return script


@pytest.fixture
def make_result() -> MakeResult:
    return write_result


@pytest.fixture
def sqlite_url(tmp_path: Path) -> str:
    database = tmp_path / 'takt.db'
    return f'sqlite:///{database}'


@pytest.fixture
def count_suites() -> CountSuites:
    return suite_count


def write_result(
    path: Path | str,
    name: str,
    values: Sequence[float],
) -> Path:
    worker_run = pyperf.Run(
        list(values),
        metadata={
            'name': name,
            'unit': 'second',
            'date': '2026-09-25 10:00:00',
        },
        collect_metadata=False,
    )
    suite = pyperf.BenchmarkSuite([pyperf.Benchmark([worker_run])])
    suite.dump(str(path))
    return Path(path)


def suite_count(url: str) -> int:
    engine = sa.create_engine(url, poolclass=sa.pool.NullPool)
    count = _count_rows(engine)
    engine.dispose()
    return count


def _count_rows(engine: sa.Engine) -> int:
    if not sa.inspect(engine).has_table('takt_suite'):
        return 0
    with engine.connect() as connection:
        count: int = connection.execute(
            sa.text('SELECT COUNT(*) FROM takt_suite'),
        ).scalar_one()
    return count
