"""Check that list arguments of the public API are not plain strings."""

from collections.abc import Sequence

from takt.domain.errors.usage_error import UsageError


def reject_single_strings(**arguments: Sequence[object]) -> None:
    """Raise if a string is passed where a sequence of strings is expected.

    A ``str`` is itself a sequence of strings, so without this check
    ``db='sqlite:///a.db'`` would be split into characters.

    :param arguments: Parameter names mapped to their values.
    :raises UsageError: If any value is a ``str``.
    """
    for name, argument in arguments.items():
        if isinstance(argument, str):
            message = (
                f'{name} must be a sequence of strings, not a single string'
            )
            raise UsageError(message)
