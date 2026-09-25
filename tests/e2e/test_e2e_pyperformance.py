from pathlib import Path

import pyperf
import pytest

from takt.cli.main import main
from tests.e2e.conftest import CountSuites


@pytest.mark.slow
def test_pyperformance_single_benchmark(
    sqlite_url: str,
    count_suites: CountSuites,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # pyperformance passes only HOME and PATH to pip, so HOME keeps its cache.
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))

    code = main(['run', '-b', 'nbody', '--fast', '--db', sqlite_url])

    result_files = list(tmp_path.glob('takt-*.json'))
    assert code == 0
    assert count_suites(sqlite_url) == 1
    assert len(result_files) == 1
    suite = pyperf.BenchmarkSuite.load(str(result_files[0]))
    assert 'nbody' in suite.get_benchmark_names()
