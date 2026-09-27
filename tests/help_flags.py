"""Flags listed in argparse ``--help`` output."""

import re

_FLAG_PATTERN = re.compile(r'(?<![\w-])--?[A-Za-z][\w-]*')
"""Short or long flag that does not follow a word character or a dash."""


def help_flags(text: str) -> set[str]:
    """Collect every flag mentioned in help text.

    :param text: Output of ``--help`` printed without colors.
    :returns: Flags such as ``-h`` and ``--output``.
    """
    return set(_FLAG_PATTERN.findall(text))
