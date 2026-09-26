import runpy
import shutil
import sys
from pathlib import Path

import pytest

import takt
from tests.compiled_name import COMPILED_NAME
from tests.conftest import PACKAGE_ROOT

CONFTEST = Path(__file__).parent / 'conftest.py'


def test_conftest_guards_the_imported_package() -> None:
    assert PACKAGE_ROOT.resolve() == Path(takt.__file__).resolve().parent


def test_conftest_stops_before_importing_takt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_dir = tmp_path / 'tests'
    package = tmp_path / 'src' / 'takt'
    tests_dir.mkdir()
    package.mkdir(parents=True)
    (package / COMPILED_NAME).touch()
    shutil.copy(CONFTEST, tests_dir)
    for name in tuple(sys.modules):
        if name.partition('.')[0] == 'takt':
            monkeypatch.setitem(sys.modules, name, None)

    with pytest.raises(SystemExit):
        runpy.run_path(str(tests_dir / CONFTEST.name))
