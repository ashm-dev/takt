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
    """Benchmark name."""

    unit: str | None = None
    """Unit of the values: ``second``, ``byte`` or ``integer``."""

    loops: int | None = None
    """Number of outer loop iterations per value."""

    inner_loops: int | None = None
    """Number of inner loop iterations per outer iteration."""

    date: str | None = None
    """Date and time when the run started, as pyperf wrote it."""

    duration: float | None = None
    """Wall time of the worker run in seconds."""

    timer: str | None = None
    """Clock used for timing and its resolution."""

    tags: tuple[str, ...] | None = None
    """Tags that group benchmarks, e.g. for pyperformance."""

    description: str | None = None
    """Free text description of the benchmark."""

    calibrate_loops: int | None = None
    """Loop count found by a calibration run."""

    recalibrate_loops: int | None = None
    """Loop count found by a recalibration run."""

    calibrate_warmups: int | None = None
    """Warmup count found by a calibration run."""

    recalibrate_warmups: int | None = None
    """Warmup count found by a recalibration run."""

    python_version: str | None = None
    """Version of the Python that ran the benchmark."""

    python_implementation: str | None = None
    """Python implementation, e.g. ``cpython`` or ``pypy``."""

    python_executable: str | None = None
    """Path to the Python executable that ran the benchmark."""

    python_compiler: str | None = None
    """Compiler that built the Python."""

    python_cflags: str | None = None
    """C compiler flags used to build the Python."""

    python_config_args: str | None = None
    """``configure`` arguments used to build the Python."""

    python_hash_seed: str | None = None
    """Value of ``PYTHONHASHSEED`` in the worker."""

    python_gc: str | None = None
    """State of the garbage collector during the run."""

    mem_max_rss: int | None = None
    """Peak resident memory of the worker in bytes."""

    command_max_rss: int | None = None
    """Peak resident memory of the timed command in bytes."""

    mem_peak_pagefile_usage: int | None = None
    """Peak pagefile usage of the worker on Windows in bytes."""

    cpu_count: int | None = None
    """Number of logical CPUs of the machine."""

    cpu_affinity: str | None = None
    """CPUs the worker was pinned to."""

    cpu_config: str | None = None
    """CPU settings such as the frequency governor and isolated CPUs."""

    cpu_freq: str | None = None
    """CPU frequencies at the time of the run."""

    cpu_machine: str | None = None
    """Machine architecture, e.g. ``x86_64``."""

    cpu_model_name: str | None = None
    """CPU model name."""

    cpu_temp: str | None = None
    """CPU temperatures at the time of the run."""

    aslr: str | None = None
    """Address space layout randomization setting of the system."""

    hostname: str | None = None
    """Host name of the machine that ran the benchmark."""

    platform: str | None = None
    """Operating system description."""

    boot_time: str | None = None
    """Time when the machine was booted."""

    uptime: float | None = None
    """Time since the machine was booted in seconds."""

    load_avg_1min: float | None = None
    """System load average over the last minute."""

    runnable_threads: int | None = None
    """Number of runnable threads on the system."""

    perf_version: str | None = None
    """Version of pyperf that ran the benchmark."""

    performance_version: str | None = None
    """Version of pyperformance that ran the benchmark."""

    timeit_stmt: str | None = None
    """Statement timed by ``pyperf timeit``."""

    timeit_setup: str | None = None
    """Setup code of ``pyperf timeit``."""

    timeit_teardown: str | None = None
    """Teardown code of ``pyperf timeit``."""

    timeit_duplicate: int | None = None
    """Number of times ``pyperf timeit`` repeats the statement per loop."""

    commit_id: str | None = None
    """Commit of the Python that pyperformance built."""

    commit_branch: str | None = None
    """Branch of the Python that pyperformance built."""

    commit_date: str | None = None
    """Date of the commit of the Python that pyperformance built."""

    patch_file: str | None = None
    """Patch applied to the Python that pyperformance built."""

    hooks: str | None = None
    """pyperf hooks enabled during the run."""

    custom: Mapping[str, MetadataValue] = field(default_factory=dict)
    """Unknown keys and known keys whose value has an unexpected type."""
