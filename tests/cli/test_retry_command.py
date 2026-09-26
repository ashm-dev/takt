import argparse
import shlex
from pathlib import Path

from takt.cli.parser import build_parser
from takt.cli.retry_command import build_retry_command


def test_example_from_spec() -> None:
    args = argparse.Namespace(
        db=['sqlite:///a.db'],
        target=['pg ci'],
        config=None,
        name='nightly {date}',
    )

    command = build_retry_command(args, Path('r.json'))

    assert command == (
        "takt import r.json --db sqlite:///a.db --target 'pg ci' "
        "--name 'nightly {date}'"
    )


def test_only_path() -> None:
    args = argparse.Namespace(db=[], target=[], config=None, name=None)

    assert build_retry_command(args, Path('r.json')) == 'takt import r.json'


def test_config_path() -> None:
    args = argparse.Namespace(
        db=[],
        target=['ci'],
        config=Path('conf/ci.toml'),
        name=None,
    )

    command = build_retry_command(args, Path('r.json'))

    assert command == 'takt import r.json --target ci --config conf/ci.toml'


def test_parser_accepts_command() -> None:
    args = argparse.Namespace(
        db=['sqlite:///a.db'],
        target=['pg ci'],
        config=Path('conf/ci.toml'),
        name='nightly {date}',
    )

    words = shlex.split(build_retry_command(args, Path('r.json')))
    parsed = build_parser().parse_args(words[1:])

    assert parsed.path == Path('r.json')
    assert parsed.db == args.db
    assert parsed.target == args.target
    assert parsed.config == args.config
    assert parsed.name == args.name
