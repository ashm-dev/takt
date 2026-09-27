import importlib

import pytest

PACKAGES = (
    'takt',
    'takt.domain',
    'takt.domain.model',
    'takt.domain.errors',
    'takt.domain.hashing',
    'takt.domain.naming',
    'takt.domain.operand',
    'takt.domain.compare',
    'takt.application',
    'takt.application.ports',
    'takt.application.multi_target',
    'takt.application.use_cases',
    'takt.infrastructure',
    'takt.infrastructure.clock',
    'takt.infrastructure.pyperf',
    'takt.infrastructure.runner',
    'takt.infrastructure.config',
    'takt.infrastructure.db',
    'takt.infrastructure.db.schema',
    'takt.infrastructure.cache',
    'takt.infrastructure.render',
    'takt.cli',
)
"""Packages that must import without errors."""


@pytest.mark.parametrize('package', PACKAGES)
def test_package_imports(package: str) -> None:
    module = importlib.import_module(package)

    assert module.__name__ == package
