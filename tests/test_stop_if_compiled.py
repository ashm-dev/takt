import shlex
from pathlib import Path

import pytest

from tests.compiled_name import COMPILED_NAME
from tests.stop_if_compiled import stop_if_compiled


def test_passes_without_compiled_modules(tmp_path: Path) -> None:
    (tmp_path / 'module.py').touch()

    stop_if_compiled(tmp_path)


def test_stops_on_nested_compiled_module(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    package = tmp_path / 'domain'
    package.mkdir()
    (package / COMPILED_NAME).touch()

    with pytest.raises(SystemExit) as exit_info:
        stop_if_compiled(tmp_path)

    assert exit_info.value.code == 2
    quoted_root = shlex.quote(str(tmp_path))
    assert f"find {quoted_root} -name '*.so' -delete" in capsys.readouterr().err
