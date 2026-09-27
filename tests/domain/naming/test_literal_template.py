from datetime import UTC, datetime
from pathlib import Path

import pytest

from takt.domain.naming.literal_template import literal_template
from takt.domain.naming.name_template import NameTemplate
from takt.domain.naming.name_values import NameValues

LATER = NameValues(
    now=datetime(2026, 9, 27, 1, 0, 0, tzinfo=UTC),
    result_path=Path('other.json'),
    python_version=None,
    hostname=None,
    suite_hash='9c01de'.ljust(64, '0'),
)
"""Values that would change any placeholder rendered at save time."""


@pytest.mark.parametrize(
    'name',
    ['nightly 2026-09-26', 'build {date} }{', 'a {{b}}'],
)
def test_renders_the_same_name_later(name: str) -> None:
    template = NameTemplate.parse(literal_template(name))

    assert template.render(LATER) == name
