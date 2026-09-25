"""Placeholders allowed in a run name template."""

from enum import StrEnum


class Placeholder(StrEnum):
    """Substitution allowed inside a run name template."""

    DATE = 'date'
    DATETIME = 'datetime'
    PATH = 'path'
    PYTHON_VERSION = 'python_version'
    HOSTNAME = 'hostname'
    HASH = 'hash'
