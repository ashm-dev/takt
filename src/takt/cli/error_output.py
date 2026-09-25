"""Printing of error messages to standard error."""

import sys


def print_error(message: str) -> None:
    """Write ``error: <message>`` as a line to standard error.

    :param message: Error text, possibly spanning several lines.
    """
    sys.stderr.write(f'error: {message}\n')
