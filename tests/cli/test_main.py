import functools
from collections.abc import Callable
from pathlib import Path

import pytest

from takt import api
from takt.application.multi_target.target_outcome import TargetOutcome
from takt.application.multi_target.target_status import TargetStatus
from takt.application.multi_target.write_report import WriteReport
from takt.application.use_cases.import_report import ImportReport
from takt.cli.main import main
from takt.domain.compare.compare_table import CompareTable
from takt.domain.errors.configuration_error import ConfigurationError
from takt.domain.errors.operand_not_found_error import OperandNotFoundError
from takt.domain.model.target import Target

NO_TARGETS = (
    'no database targets configured: use --db, --target, TAKT_DB or takt.toml'
)
LOCAL = Target(name='local', url='sqlite:///a.db', dialect='sqlite')
MARIA = Target(
    name=None,
    url='mariadb+pymysql://u:secret@h/db',
    dialect='mariadb',
)
SNAPSHOT_TABLE = CompareTable(
    headers=('Benchmark', 'base.json', 'new.json'),
    rows=(('nbody', '100 ms', '90.0 ms: 1.11x faster'),),
    hidden_not_significant=(),
    ignored=(),
)
SNAPSHOT_MARKDOWN = (
    '| Benchmark | base.json | new.json              |\n'
    '|-----------|:---------:|:---------------------:|\n'
    '| nbody     | 100 ms    | 90.0 ms: 1.11x faster |\n'
)


class Recorder:
    def __init__(self, response: object) -> None:
        self.response = response
        self.args: tuple[object, ...] = ()
        self.kwargs: dict[str, object] = {}

    def __call__(self, *args: object, **kwargs: object) -> object:
        self.args = args
        self.kwargs = kwargs
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def import_report(*outcomes: TargetOutcome) -> ImportReport:
    return ImportReport(
        result_path=Path('r.json'),
        suite_hash='3fa2b1c4d5e6'.ljust(64, '0'),
        name='default',
        write=WriteReport(outcomes=outcomes),
    )


def written(target: Target) -> TargetOutcome:
    return TargetOutcome(
        target=target,
        status=TargetStatus.WRITTEN,
        existing_name=None,
        error=None,
    )


OK_REPORT = import_report(written(LOCAL))
FAILED_REPORT = import_report(
    TargetOutcome(
        target=LOCAL,
        status=TargetStatus.ROLLED_BACK,
        existing_name=None,
        error=None,
    ),
    TargetOutcome(
        target=MARIA,
        status=TargetStatus.FAILED,
        existing_name=None,
        error='connection refused',
    ),
)


@pytest.fixture
def fake_api(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[str, object], Recorder]:
    return functools.partial(_install, monkeypatch)


def _install(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
    response: object,
) -> Recorder:
    recorder = Recorder(response)
    monkeypatch.setattr(api, function_name, recorder)
    return recorder


def test_import_ok(fake_api: Callable[[str, object], Recorder]) -> None:
    fake = fake_api('import_results', OK_REPORT)

    code = main(['import', 'r.json', '--db', 'sqlite:///a.db'])

    assert code == 0
    assert fake.args == (Path('r.json'),)
    assert fake.kwargs['db'] == ['sqlite:///a.db']


def test_import_failed_write(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api('import_results', FAILED_REPORT)

    code = main(['import', 'r.json', '--db', 'sqlite:///a.db'])

    assert code == 1
    assert capsys.readouterr().err == (
        'error: result was not written to all targets\n'
    )


def test_run_failed_write_prints_retry(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = fake_api('run', FAILED_REPORT)

    code = main(
        ['run', '-b', 'nbody', '--db', 'sqlite:///a.db', '--name', 'x'],
    )

    assert code == 1
    assert fake.args == (('-b', 'nbody'),)
    assert (
        'Retry without re-running benchmarks: '
        'takt import r.json --db sqlite:///a.db --name x'
    ) in capsys.readouterr().err.splitlines()


def test_takt_error_exit_code(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_api('import_results', ConfigurationError(NO_TARGETS))

    code = main(['import', 'r.json'])

    assert code == 2
    assert capsys.readouterr().err == f'error: {NO_TARGETS}\n'


def test_execution_error_exit_code(
    fake_api: Callable[[str, object], Recorder],
) -> None:
    fake_api(
        'compare',
        OperandNotFoundError(
            "operand 'x' not found: no file, run name or hash prefix matches",
        ),
    )

    assert main(['compare', 'x', 'y']) == 1


def test_keyboard_interrupt(
    fake_api: Callable[[str, object], Recorder],
) -> None:
    fake_api('run', KeyboardInterrupt())

    assert main(['run', '--db', 'sqlite:///a.db']) == 130


def test_unknown_flag_for_import(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(['import', 'r.json', '--fast'])

    assert error.value.code == 2
    assert 'unrecognized arguments: --fast' in capsys.readouterr().err


def test_compare_writes_markdown(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    fake_api('compare', SNAPSHOT_TABLE)
    markdown = tmp_path / 'out.md'

    code = main(['compare', 'a', 'b', '--markdown', str(markdown)])

    assert code == 0
    assert markdown.read_text(encoding='utf-8') == SNAPSHOT_MARKDOWN
    assert 'Markdown table written to' in capsys.readouterr().out


def test_compare_markdown_write_error(
    fake_api: Callable[[str, object], Recorder],
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    fake_api('compare', SNAPSHOT_TABLE)
    markdown = tmp_path / 'missing' / 't.md'

    code = main(['compare', 'a', 'b', '--markdown', str(markdown)])

    assert code == 1
    assert capsys.readouterr().err.startswith(
        'error: cannot write markdown file',
    )


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(['--version'])

    assert error.value.code == 0
    assert capsys.readouterr().out.startswith('takt ')
