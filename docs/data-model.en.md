# Data model

This page describes the tables takt creates in every target database.
Use it to write your own SQL queries and dashboards over the stored results.

## Tables

All tables start with `takt_`, so they do not clash with your own tables in a shared database.
takt stores only these tables; it does not keep the raw JSON file.

```text
takt_suite            one row per stored result
└─ takt_benchmark     one row per benchmark in the result
   └─ takt_worker_run one row per pyperf worker run of the benchmark
      ├─ takt_measurement   one row per measured value or warmup value
      └─ takt_run_metadata  one row of metadata per worker run
takt_loaded_hash      hashes of stored results
takt_alembic_version  schema version
```

Keys are made of several columns and have no auto-increment.
Every child table has `suite_hash`, so all rows of one result can be found by its hash.
All positions start at 0 and follow the order in the result file.

### takt_suite

One stored result, that is one pyperf JSON file.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `hash` | CHAR(64) | no | Primary key. SHA-256 of the result |
| `name` | VARCHAR(255) | yes | Run name; NULL if no name was given |
| `format_version` | VARCHAR(16) | no | pyperf file format version: `1.0`, `5` or `6` |
| `source` | VARCHAR(16) | no | `run` or `import`: the command that stored the result |
| `result_date` | DATETIME | yes | Earliest `date` of the worker runs, local time of the benchmark machine without a time zone |
| `loaded_at` | DATETIME | no | When takt stored the result, UTC without a time zone |

Indexes: `name`, `result_date`.

### takt_benchmark

One benchmark inside a result.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `suite_hash` | CHAR(64) | no | Primary key part; refers to `takt_suite.hash` |
| `benchmark_position` | INTEGER | no | Primary key part; position of the benchmark in the file |
| `name` | VARCHAR(255) | no | Benchmark name, for example `nbody` |

### takt_worker_run

One run of a pyperf worker process: one element of `runs` in the result file.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `suite_hash` | CHAR(64) | no | Primary key part |
| `benchmark_position` | INTEGER | no | Primary key part |
| `run_position` | INTEGER | no | Primary key part; position of the run inside the benchmark |

`(suite_hash, benchmark_position)` refers to `takt_benchmark`.

### takt_measurement

One measured value or one warmup value.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `suite_hash` | CHAR(64) | no | Primary key part |
| `benchmark_position` | INTEGER | no | Primary key part |
| `run_position` | INTEGER | no | Primary key part |
| `kind` | VARCHAR(8) | no | Primary key part; `value` for a measurement, `warmup` for a warmup |
| `position` | INTEGER | no | Primary key part; position among values of the same kind |
| `loops` | INTEGER | yes | Number of loops of a warmup; NULL for `value` |
| `value` | DOUBLE | no | The value in the benchmark unit (`unit` in metadata), per loop |

`(suite_hash, benchmark_position, run_position)` refers to `takt_worker_run`.
Calibration runs have only `warmup` rows.

### takt_run_metadata

Metadata of one worker run.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `suite_hash` | CHAR(64) | no | Primary key part |
| `benchmark_position` | INTEGER | no | Primary key part |
| `run_position` | INTEGER | no | Primary key part |
| one column per known pyperf key | see below | yes | Value of that key; NULL if the run does not have it |
| `custom` | JSON | yes | All other keys as a JSON object; NULL if there are none |

`(suite_hash, benchmark_position, run_position)` refers to `takt_worker_run`.

A column has the same name as the pyperf key:

| Type | Columns |
|---|---|
| BIGINT | `loops`, `inner_loops`, `calibrate_loops`, `recalibrate_loops`, `calibrate_warmups`, `recalibrate_warmups`, `mem_max_rss`, `command_max_rss`, `mem_peak_pagefile_usage`, `cpu_count`, `runnable_threads`, `timeit_duplicate` |
| DOUBLE | `duration`, `uptime`, `load_avg_1min` |
| JSON | `tags` (list of strings) |
| TEXT | `name`, `unit`, `date`, `timer`, `description`, `python_version`, `python_implementation`, `python_executable`, `python_compiler`, `python_cflags`, `python_config_args`, `python_hash_seed`, `python_gc`, `cpu_affinity`, `cpu_config`, `cpu_freq`, `cpu_machine`, `cpu_model_name`, `cpu_temp`, `aslr`, `hostname`, `platform`, `boot_time`, `perf_version`, `performance_version`, `timeit_stmt`, `timeit_setup`, `timeit_teardown`, `commit_id`, `commit_branch`, `commit_date`, `patch_file`, `hooks` |

### takt_loaded_hash

Hashes of all stored results.
takt uses it to check quickly whether a result is already in the database.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `hash` | CHAR(64) | no | Primary key. Same value as `takt_suite.hash` |

### takt_alembic_version

The schema version of this database.
takt reads and updates it itself; do not change it.

## Metadata rule

In a pyperf file, a metadata key that is the same for all runs is written once at the benchmark level or at the file level.
takt undoes this: every row of `takt_run_metadata` has the full set of keys of its worker run, including the keys written at the upper levels.
So you can filter by any key, for example `hostname` or `python_version`, without joining other levels.

A key that is not in the table above, or whose value has an unexpected type, goes to `custom`.
For example, keys added with `pyperf.Runner(metadata=...)` are in `custom`.

## Example query

The mean value of the `nbody` benchmark for every run named `baseline`:

```sql
SELECT s.name, s.result_date, AVG(m.value) AS mean_seconds
FROM takt_suite s
JOIN takt_measurement m ON m.suite_hash = s.hash
JOIN takt_benchmark b ON b.suite_hash = m.suite_hash AND b.benchmark_position = m.benchmark_position
WHERE b.name = 'nbody' AND m.kind = 'value' AND s.name = 'baseline'
GROUP BY s.hash, s.name, s.result_date
ORDER BY s.result_date;
```
