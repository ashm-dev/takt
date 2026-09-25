"""Metadata of one pyperf worker run."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from takt.domain.model.metadata_value import MetadataValue


@dataclass(frozen=True, kw_only=True)
class RunMetadata:
    """Full metadata of one worker run.

    Every field is a known pyperf or pyperformance key with the same name.
    Unknown keys and known keys with an unexpected type live in ``custom``.
    """

    name: str | None = None
    unit: str | None = None
    loops: int | None = None
    inner_loops: int | None = None
    date: str | None = None
    duration: float | None = None
    timer: str | None = None
    tags: tuple[str, ...] | None = None
    description: str | None = None
    calibrate_loops: int | None = None
    recalibrate_loops: int | None = None
    calibrate_warmups: int | None = None
    recalibrate_warmups: int | None = None
    python_version: str | None = None
    python_implementation: str | None = None
    python_executable: str | None = None
    python_compiler: str | None = None
    python_cflags: str | None = None
    python_config_args: str | None = None
    python_hash_seed: str | None = None
    python_gc: str | None = None
    mem_max_rss: int | None = None
    command_max_rss: int | None = None
    mem_peak_pagefile_usage: int | None = None
    cpu_count: int | None = None
    cpu_affinity: str | None = None
    cpu_config: str | None = None
    cpu_freq: str | None = None
    cpu_machine: str | None = None
    cpu_model_name: str | None = None
    cpu_temp: str | None = None
    aslr: str | None = None
    hostname: str | None = None
    platform: str | None = None
    boot_time: str | None = None
    uptime: float | None = None
    load_avg_1min: float | None = None
    runnable_threads: int | None = None
    perf_version: str | None = None
    performance_version: str | None = None
    timeit_stmt: str | None = None
    timeit_setup: str | None = None
    timeit_teardown: str | None = None
    timeit_duplicate: int | None = None
    commit_id: str | None = None
    commit_branch: str | None = None
    commit_date: str | None = None
    patch_file: str | None = None
    hooks: str | None = None
    custom: Mapping[str, MetadataValue] = field(default_factory=dict)
