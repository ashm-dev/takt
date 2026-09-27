import importlib

import pytest

PORT_MODULES = (
    'takt.application.ports.benchmark_runner',
    'takt.application.ports.clock',
    'takt.application.ports.result_reader',
    'takt.application.ports.schema_migrator',
    'takt.application.ports.schema_version_cache',
    'takt.application.ports.target_connector',
    'takt.application.ports.target_session',
)
"""Port modules that must import without errors."""


@pytest.mark.parametrize('module_name', PORT_MODULES)
def test_port_module_imports(module_name: str) -> None:
    module = importlib.import_module(module_name)

    assert module.__name__ == module_name
