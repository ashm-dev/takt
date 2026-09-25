import pytest

from takt.domain.model.target import Target


def test_display_prefers_target_name() -> None:
    target = Target(
        name='local',
        url='sqlite:///bench.db',
        dialect='sqlite',
    )

    assert target.display() == 'local'


@pytest.mark.parametrize(
    ('url', 'expected'),
    [
        (
            'mariadb+pymysql://user:secret@db.example:3306/bench',
            'mariadb+pymysql://user:***@db.example:3306/bench',
        ),
        ('sqlite:///bench.db', 'sqlite:///bench.db'),
    ],
)
def test_display_hides_password(url: str, expected: str) -> None:
    target = Target(name=None, url=url, dialect='mariadb')

    assert target.display() == expected
