"""Value type of every metadata key that has its own field."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, TypeAlias

from takt.domain.model.metadata_value import MetadataValue

_KeyType: TypeAlias = type[MetadataValue]
"""Python type that the value of a known metadata key must have."""

METADATA_KEY_TYPES: Final[Mapping[str, _KeyType]] = MappingProxyType(
    {
        'name': str,
        'unit': str,
        'loops': int,
        'inner_loops': int,
        'date': str,
        'duration': float,
        'timer': str,
        'tags': tuple,
        'description': str,
        'calibrate_loops': int,
        'recalibrate_loops': int,
        'calibrate_warmups': int,
        'recalibrate_warmups': int,
        'python_version': str,
        'python_implementation': str,
        'python_executable': str,
        'python_compiler': str,
        'python_cflags': str,
        'python_config_args': str,
        'python_hash_seed': str,
        'python_gc': str,
        'mem_max_rss': int,
        'command_max_rss': int,
        'mem_peak_pagefile_usage': int,
        'cpu_count': int,
        'cpu_affinity': str,
        'cpu_config': str,
        'cpu_freq': str,
        'cpu_machine': str,
        'cpu_model_name': str,
        'cpu_temp': str,
        'aslr': str,
        'hostname': str,
        'platform': str,
        'boot_time': str,
        'uptime': float,
        'load_avg_1min': float,
        'runnable_threads': int,
        'perf_version': str,
        'performance_version': str,
        'timeit_stmt': str,
        'timeit_setup': str,
        'timeit_teardown': str,
        'timeit_duplicate': int,
        'commit_id': str,
        'commit_branch': str,
        'commit_date': str,
        'patch_file': str,
        'hooks': str,
    }
)
"""Expected value type of every key that has its own ``RunMetadata`` field."""
