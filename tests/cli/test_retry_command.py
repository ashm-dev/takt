import argparse
from pathlib import Path

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
