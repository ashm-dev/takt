from pathlib import Path

import pytest

from takt.cli.main import main
from takt.cli.parser import build_parser


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
