"""Placeholders allowed in a run name template."""

from enum import StrEnum


class Placeholder(StrEnum):
    """Substitution allowed inside a run name template."""

    DATE = 'date'
    """UTC date of ``now`` as ``YYYY-MM-DD``."""

    DATETIME = 'datetime'
    """UTC time of ``now`` as ``YYYY-MM-DDTHH-MM-SSZ``."""

    PATH = 'path'
    """Result file name without ``.json`` or ``.json.gz``."""

    PYTHON_VERSION = 'python_version'
    """Python version from the result, or ``unknown``."""

    HOSTNAME = 'hostname'
    """Host name from the result, or ``unknown``."""

    HASH = 'hash'
    """First 12 characters of the suite hash."""
