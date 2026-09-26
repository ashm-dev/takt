from pathlib import Path

import pytest

from takt.cli.main import main
from takt.cli.parser import build_parser
from takt.infrastructure.runner.takt_flags import TAKT_FLAGS
from tests.help_flags import help_flags


def test_run_passes_unknown_flags() -> None:
    args, extra = build_parser().parse_known_args(
        ['run', '-b', 'nbody', '--db', 'sqlite:///a.db', '--fast'],
    )

    assert args.db == ['sqlite:///a.db']
    assert extra == ['-b', 'nbody', '--fast']


def test_run_script_path_is_extra() -> None:
    args, extra = build_parser().parse_known_args(
        ['run', 'bench.py', '--values', '3', '--target', 'local'],
    )

    assert extra == ['bench.py', '--values', '3']
    assert args.target == ['local']


def test_no_abbreviation() -> None:
    args, extra = build_parser().parse_known_args(['run', '--tags', 'apps'])

    assert args.target == []
    assert extra == ['--tags', 'apps']


def test_target_repeatable() -> None:
    args, _ = build_parser().parse_known_args(
        ['import', 'r.json', '--target', 'a', '--target', 'b'],
    )

    assert args.target == ['a', 'b']
    assert args.path == Path('r.json')


def test_compare_markdown() -> None:
    args, _ = build_parser().parse_known_args(
        ['compare', 'a', 'b', 'c', '--markdown', 'out.md'],
    )

    assert args.operands == ['a', 'b', 'c']
    assert args.markdown == Path('out.md')


def test_command_required() -> None:
    with pytest.raises(SystemExit) as error:
        main([])

    assert error.value.code == 2


@pytest.mark.usefixtures('no_color')
def test_run_owns_only_takt_flags(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_known_args(['run', '--help'])

    options = capsys.readouterr().out.partition('options:\n')[2]
    flags = help_flags(options.partition('\n\n')[0])
    assert flags == {'-h', '--help', *TAKT_FLAGS}


def help_text(capsys: pytest.CaptureFixture[str], command: str) -> str:
    with pytest.raises(SystemExit):
        build_parser().parse_known_args([command, '--help'])
    return ' '.join(capsys.readouterr().out.split())


@pytest.mark.usefixtures('no_color')
def test_run_help_explains_both_modes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    text = help_text(capsys, 'run')

    assert 'takt run SCRIPT.py [takt flags] [pyperf.Runner flags ...]' in text
    assert "goes unchanged to 'python -m pyperformance run'" in text
    assert '-o/--output picks the result file' in text
    assert "'python SCRIPT.py --help'" in text


@pytest.mark.usefixtures('no_color')
def test_compare_help_explains_operands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    text = help_text(capsys, 'compare')

    assert 'NAME:N' in text
    assert 'the first one is the base' in text
    assert 'only the first target is read' in text


@pytest.mark.usefixtures('no_color')
def test_import_help_explains_path(capsys: pytest.CaptureFixture[str]) -> None:
    text = help_text(capsys, 'import')

    assert 'PATH pyperf or pyperformance JSON result' in text
