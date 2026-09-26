"""Regex for ``pytest.raises`` that accepts one exact error message."""

import re


def exact_pattern(message: str) -> str:
    """Build a pattern that matches ``message`` and nothing longer.

    :param message: Expected error message.
    :returns: Escaped ``message`` anchored at both ends.
    """
    return rf'\A{re.escape(message)}\Z'
