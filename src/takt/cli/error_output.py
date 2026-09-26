"""Printing of error messages to standard error."""

import sys


def print_error(message: str) -> None:
    """Write ``error: <message>`` as a line to standard error.

    Standard output is flushed first, so that in a CI log the report that
    explains the error comes before it.

    :param message: Error text, possibly spanning several lines.
    """
    sys.stdout.flush()
    sys.stderr.write(f'error: {message}\n')
